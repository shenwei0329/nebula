# -*- coding: utf-8 -*-

import functools
import logging
import re
import time
import contextlib

import six
from flask import _app_ctx_stack
import sqlalchemy.engine
import sqlalchemy.engine.url
import sqlalchemy.event
import sqlalchemy.orm
import sqlalchemy.orm.session
from sqlalchemy.orm import persistence
from sqlalchemy import inspect
from oslo_config import cfg
from sqlalchemy import exc as sqla_exc
from sqlalchemy.interfaces import PoolListener
from sqlalchemy.pool import NullPool
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.expression import literal_column

from nebula.core.db import exception
from nebula.core.i18n import _

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CONF.import_group('portal', 'nebula.portal.options')


class SqliteForeignKeysListener(PoolListener):
    """Ensures that the foreign key constraints are enforced in SQLite.

    The foreign key constraints are disabled by default in SQLite,
    so the foreign key constraints will be enabled here for every
    database connection
    """

    def connect(self, dbapi_con, con_record):
        dbapi_con.execute('pragma foreign_keys=ON')

_DUP_KEY_RE_DB = {
    "sqlite": (re.compile(r"^.*columns?([^)]+)(is|are)\s+not\s+unique$"),
               re.compile(r"^.*UNIQUE\s+constraint\s+failed:\s+(.+)$")),
    "postgresql": (re.compile(r"^.*duplicate\s+key.*\"([^\"]+)\"\s*\n.*$"),),
    "mysql": (re.compile(r"^.*\(1062,.*'([^\']+)'\"\)$"),),
    "ibm_db_sa": (re.compile(r"^.*SQL0803N.*$"),),
}

def _raise_if_duplicate_entry_error(integrity_error, engine_name):
    """Raise exception if two entries are duplicated.

    In this function will be raised DBDuplicateEntry exception if integrity
    error wrap unique constraint violation.
    """

    def get_columns_from_uniq_cons_or_name(columns):
        # note(vsergeyev): UniqueConstraint name convention: "uniq_t0c10c2"
        #                  where `t` it is table name and columns `c1`, `c2`
        #                  are in UniqueConstraint.
        uniqbase = "uniq_"
        if not columns.startswith(uniqbase):
            if engine_name == "postgresql":
                return [columns[columns.index("_") + 1:columns.rindex("_")]]
            return [columns]
        return columns[len(uniqbase):].split("0")[1:]

    if engine_name not in ["ibm_db_sa", "mysql", "sqlite", "postgresql"]:
        return

    # FIXME(johannes): The usage of the .message attribute has been
    # deprecated since Python 2.6. However, the exceptions raised by
    # SQLAlchemy can differ when using unicode() and accessing .message.
    # An audit across all three supported engines will be necessary to
    # ensure there are no regressions.
    for pattern in _DUP_KEY_RE_DB[engine_name]:
        match = pattern.match(integrity_error.message)
        if match:
            break
    else:
        return

    # NOTE(mriedem): The ibm_db_sa integrity error message doesn't provide the
    # columns so we have to omit that from the DBDuplicateEntry error.
    columns = ''

    if engine_name != 'ibm_db_sa':
        columns = match.group(1)

    if engine_name == "sqlite":
        columns = [c.split('.')[-1] for c in columns.strip().split(", ")]
    else:
        columns = get_columns_from_uniq_cons_or_name(columns)
    raise exception.DBDuplicateEntry(columns, integrity_error)


# NOTE(comstud): In current versions of DB backends, Deadlock violation
# messages follow the structure:
#
# mysql:
# (OperationalError) (1213, 'Deadlock found when trying to get lock; try '
#                     'restarting transaction') <query_str> <query_args>
_DEADLOCK_RE_DB = {
    "mysql": re.compile(r"^.*\(1213, 'Deadlock.*")
}


def _raise_if_deadlock_error(operational_error, engine_name):
    """Raise exception on deadlock condition.

    Raise DBDeadlock exception if OperationalError contains a Deadlock
    condition.
    """
    re = _DEADLOCK_RE_DB.get(engine_name)
    if re is None:
        return
    # FIXME(johannes): The usage of the .message attribute has been
    # deprecated since Python 2.6. However, the exceptions raised by
    # SQLAlchemy can differ when using unicode() and accessing .message.
    # An audit across all three supported engines will be necessary to
    # ensure there are no regressions.
    m = re.match(operational_error.message)
    if not m:
        return
    raise exception.DBDeadlock(operational_error)


def _wrap_db_error(f):
    @functools.wraps(f)
    def _wrap(self, *args, **kwargs):
        try:
            assert issubclass(
                self.__class__, sqlalchemy.orm.session.Session
            ), ('_wrap_db_error() can only be applied to methods of '
                'subclasses of sqlalchemy.orm.session.Session.')

            return f(self, *args, **kwargs)
        except UnicodeEncodeError:
            raise exception.DBInvalidUnicodeParameter()
        except sqla_exc.OperationalError as e:
            _raise_if_db_connection_lost(e, self.bind)
            _raise_if_deadlock_error(e, self.bind.dialect.name)
            # NOTE(comstud): A lot of code is checking for OperationalError
            # so let's not wrap it for now.
            raise
        # note(boris-42): We should catch unique constraint violation and
        # wrap it by our own DBDuplicateEntry exception. Unique constraint
        # violation is wrapped by IntegrityError.
        except sqla_exc.IntegrityError as e:
            # note(boris-42): SqlAlchemy doesn't unify errors from different
            # DBs so we must do this. Also in some tables (for example
            # instance_types) there are more than one unique constraint. This
            # means we should get names of columns, which values violate
            # unique constraint, from error message.
            _raise_if_duplicate_entry_error(e, self.bind.dialect.name)
            raise exception.DBError(e)
        except Exception as e:
            LOG.exception(_('DB exception wrapped.'))
            raise exception.DBError(e)

    return _wrap


def _synchronous_switch_listener(dbapi_conn, connection_rec):
    """Switch sqlite connections to non-synchronous mode."""
    dbapi_conn.execute("PRAGMA synchronous = OFF")


def _add_regexp_listener(dbapi_con, con_record):
    """Add REGEXP function to sqlite connections."""

    def regexp(expr, item):
        reg = re.compile(expr)
        return reg.search(six.text_type(item)) is not None

    dbapi_con.create_function('regexp', 2, regexp)


def _thread_yield(dbapi_con, con_record):
    """Ensure other greenthreads get a chance to be executed.

    If we use eventlet.monkey_patch(), eventlet.greenthread.sleep(0) will
    execute instead of time.sleep(0).
    Force a context switch. With common database backends (eg MySQLdb and
    sqlite), there is no implicit yield caused by network I/O since they are
    implemented by C libraries that eventlet cannot monkey patch.
    """
    time.sleep(0)


def _ping_listener(engine, dbapi_conn, connection_rec, connection_proxy):
    """Ensures that MySQL and DB2 connections are alive.

    Borrowed from:
    http://groups.google.com/group/sqlalchemy/msg/a4ce563d802c929f
    """
    cursor = dbapi_conn.cursor()
    try:
        ping_sql = 'select 1'
        if engine.name == 'ibm_db_sa':
            # DB2 requires a table expression
            ping_sql = 'select 1 from (values (1)) AS t1'
        cursor.execute(ping_sql)
    except Exception as ex:
        if engine.dialect.is_disconnect(ex, dbapi_conn, cursor):
            msg = _('Database server has gone away: %s') % ex
            LOG.warning(msg)

            # if the database server has gone away, all connections in the pool
            # have become invalid and we can safely close all of them here,
            # rather than waste time on checking of every single connection
            engine.dispose()

            # this will be handled by SQLAlchemy and will force it to create
            # a new connection and retry the original action
            raise sqla_exc.DisconnectionError(msg)
        else:
            raise


def _set_session_sql_mode(dbapi_con, connection_rec, sql_mode=None):
    """Set the sql_mode session variable.

    MySQL supports several server modes. The default is None, but sessions
    may choose to enable server modes like TRADITIONAL, ANSI,
    several STRICT_* modes and others.

    Note: passing in '' (empty string) for sql_mode clears
    the SQL mode for the session, overriding a potentially set
    server default.
    """

    cursor = dbapi_con.cursor()
    cursor.execute("SET SESSION sql_mode = %s", [sql_mode])


def _mysql_get_effective_sql_mode(engine):
    """Returns the effective SQL mode for connections from the engine pool.

    Returns ``None`` if the mode isn't available, otherwise returns the mode.

    """
    # Get the real effective SQL mode. Even when unset by
    # our own config, the server may still be operating in a specific
    # SQL mode as set by the server configuration.
    # Also note that the checkout listener will be called on execute to
    # set the mode if it's registered.
    row = engine.execute("SHOW VARIABLES LIKE 'sql_mode'").fetchone()
    if row is None:
        return
    return row[1]


def _mysql_check_effective_sql_mode(engine):
    """Logs a message based on the effective SQL mode for MySQL connections."""
    realmode = _mysql_get_effective_sql_mode(engine)

    if realmode is None:
        LOG.warning(_('Unable to detect effective SQL mode'))
        return

    LOG.debug('MySQL server mode set to %s', realmode)
    # 'TRADITIONAL' mode enables several other modes, so
    # we need a substring match here
    if not ('TRADITIONAL' in realmode.upper() or
            'STRICT_ALL_TABLES' in realmode.upper()):
        LOG.warning(_("MySQL SQL mode is '%s', "
                        "consider enabling TRADITIONAL or STRICT_ALL_TABLES"),
                    realmode)


def _mysql_set_mode_callback(engine, sql_mode):
    if sql_mode is not None:
        mode_callback = functools.partial(_set_session_sql_mode,
                                          sql_mode=sql_mode)
        sqlalchemy.event.listen(engine, 'connect', mode_callback)
    _mysql_check_effective_sql_mode(engine)


def _is_db_connection_error(args):
    """Return True if error in connecting to db."""
    # NOTE(adam_g): This is currently MySQL specific and needs to be extended
    #               to support Postgres and others.
    # For the db2, the error code is -30081 since the db2 is still not ready
    conn_err_codes = ('2002', '2003', '2006', '2013', '-30081')
    for err_code in conn_err_codes:
        if args.find(err_code) != -1:
            return True
    return False


def _raise_if_db_connection_lost(error, engine):
    # NOTE(vsergeyev): Function is_disconnect(e, connection, cursor)
    #                  requires connection and cursor in incoming parameters,
    #                  but we have no possibility to create connection if DB
    #                  is not available, so in such case reconnect fails.
    #                  But is_disconnect() ignores these parameters, so it
    #                  makes sense to pass to function None as placeholder
    #                  instead of connection and cursor.
    if engine.dialect.is_disconnect(error, None, None):
        raise exception.DBConnectionError(error)


def create_engine(sql_connection, sqlite_fk=False, mysql_sql_mode=None,
                  idle_timeout=1800, echo=None,
                  connection_debug=0, max_pool_size=None, max_overflow=None,
                  pool_timeout=None, sqlite_synchronous=True,
                  connection_trace=False, max_retries=10, retry_interval=10,
                  **kwargs):
    """Return a new SQLAlchemy engine."""

    connection_dict = sqlalchemy.engine.url.make_url(sql_connection)

    engine_args = {
        "pool_recycle": idle_timeout,
        'convert_unicode': True,
    }

    logger = logging.getLogger('sqlalchemy.engine')

    using_scope = CONF.portal.using_scope

    if using_scope:
        LOG.info('* Updating engine strategy to threadlocal')
        engine_args['strategy'] = 'threadlocal'

    # Map SQL debug level to Python log level
    if connection_debug >= 100:
        logger.setLevel(logging.DEBUG)
    elif connection_debug >= 50:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    if "sqlite" in connection_dict.drivername:
        if sqlite_fk:
            engine_args["listeners"] = [SqliteForeignKeysListener()]
        engine_args["poolclass"] = NullPool

        if sql_connection == "sqlite://":
            engine_args["poolclass"] = StaticPool
            engine_args["connect_args"] = {'check_same_thread': False}
    else:
        if max_pool_size is not None:
            engine_args['pool_size'] = max_pool_size
        if max_overflow is not None:
            engine_args['max_overflow'] = max_overflow
        if pool_timeout is not None:
            engine_args['pool_timeout'] = pool_timeout
        if echo is not None:
            engine_args['echo'] = echo

    if kwargs.get('executor') is not None:
        engine_args.update(kwargs)
    engine = sqlalchemy.create_engine(sql_connection, **engine_args)

    if using_scope:
        LOG.info('* Updating engine pool to _use_threadlocal')
        engine.pool._use_threadlocal = True

    # Since its just a mock connection, we do not need to setup events
    if engine.__class__.__name__ == 'MockConnection':
        return engine

    sqlalchemy.event.listen(engine, 'checkin', _thread_yield)

    if engine.name in ['mysql', 'ibm_db_sa']:
        ping_callback = functools.partial(_ping_listener, engine)
        sqlalchemy.event.listen(engine, 'checkout', ping_callback)
        if engine.name == 'mysql':
            if mysql_sql_mode:
                _mysql_set_mode_callback(engine, mysql_sql_mode)
    elif 'sqlite' in connection_dict.drivername:
        if not sqlite_synchronous:
            sqlalchemy.event.listen(engine, 'connect',
                                    _synchronous_switch_listener)
        sqlalchemy.event.listen(engine, 'connect', _add_regexp_listener)

    if connection_trace and engine.dialect.dbapi.__name__ == 'MySQLdb':
        _patch_mysqldb_with_stacktrace_comments()

    try:
        engine.connect()
    except sqla_exc.OperationalError as e:
        if not _is_db_connection_error(e.args[0]):
            raise

        remaining = max_retries
        if remaining == -1:
            remaining = 'infinite'
        while True:
            msg = _('SQL connection failed. %s attempts left.')
            LOG.warning(msg % remaining)
            if remaining != 'infinite':
                remaining -= 1
            time.sleep(retry_interval)
            try:
                engine.connect()
                break
            except sqla_exc.OperationalError as e:
                if (remaining != 'infinite' and remaining == 0) or \
                        not _is_db_connection_error(e.args[0]):
                    raise
    return engine


class Query(sqlalchemy.orm.query.Query):
    """Subclass of sqlalchemy.query with soft_delete() method."""

    def soft_delete(self, synchronize_session='evaluate'):
        return self.update({'deleted': literal_column('id'),
                            'updated_at': literal_column('updated_at'),
                            },
                           synchronize_session=synchronize_session)


class Session(sqlalchemy.orm.session.Session):
    """Custom Session class to avoid SqlAlchemy Session monkey patching."""

    @_wrap_db_error
    def query(self, *args, **kwargs):
        return super(Session, self).query(*args, **kwargs)

    @_wrap_db_error
    def flush(self, *args, **kwargs):
        return super(Session, self).flush(*args, **kwargs)

    @_wrap_db_error
    def execute(self, *args, **kwargs):
        return super(Session, self).execute(*args, **kwargs)


def _get_maker(engine, autocommit=False, expire_on_commit=False,
              using_scope=False, scopefunc=None):
    """Return a SQLAlchemy sessionmaker using the given engine."""

    _sessionmaker = functools.partial(
        sqlalchemy.orm.sessionmaker, bind=engine, class_=Session, autocommit=autocommit,
        query_cls=Query, expire_on_commit=expire_on_commit, autoflush=False
    )
    if using_scope:
        return sqlalchemy.orm.scoped_session(
            _sessionmaker(), scopefunc or _app_ctx_stack.__ident_func__)
    else:
        return _sessionmaker()


class FakeUOWTransaction(object):
    def __init__(self, session):
        self.session = session


def fast_save(obj, session):
    using_scope = CONF.portal.using_scope

    if using_scope:
        state = inspect(obj)
        isinsert = state.key is None
        mapper = state.mapper
        uowtransaction = FakeUOWTransaction(session)

        with session.begin(subtransactions=True) as transaction:
            uowtransaction.transaction = transaction
            persistence.save_obj(mapper.base_mapper, [state],
                uowtransaction, single=True)
            if isinsert:
                instance_key = mapper._identity_key_from_state(state)
                state.key = instance_key
                session.identity_map.replace(state)
                session._new.pop(state)
            state._commit_all(state.dict, instance_dict=session.identity_map)
            session._register_altered([state])


def _patch_mysqldb_with_stacktrace_comments():
    """Adds current stack trace as a comment in queries.

    Patches MySQLdb.cursors.BaseCursor._do_query.
    """
    import MySQLdb.cursors
    import traceback


    old_mysql_do_query = MySQLdb.cursors.BaseCursor._do_query

    def _do_query(self, q):
        stack = ''
        for filename, line, method, function in traceback.extract_stack():
            # exclude various common things from trace
            if filename.endswith('session.py') and method == '_do_query':
                continue
            if filename.endswith('api.py') and method == 'wrapper':
                continue
            if filename.endswith('utils.py') and method == '_inner':
                continue
            if filename.endswith('exception.py') and method == '_wrap':
                continue
            # db/api is just a wrapper around db/sqlalchemy/api
            if filename.endswith('db/api.py'):
                continue
            # only trace inside nebula
            index = filename.rfind('nebula')
            if index == -1:
                continue
            stack += "File:%s:%s Method:%s() Line:%s | " \
                     % (filename[index:], line, method, function)

        # strip trailing " | " from stack
        if stack:
            stack = stack[:-3]
            qq = "%s /* %s */" % (q, stack)
        else:
            qq = q
        old_mysql_do_query(self, qq)

    setattr(MySQLdb.cursors.BaseCursor, '_do_query', _do_query)


class EngineFacade(object):
    """A helper class for removing of global engine instances from oslo.db.

    As a library, oslo.db can't decide where to store/when to create engine
    and sessionmaker instances, so this must be left for a target application.

    On the other hand, in order to simplify the adoption of oslo.db changes,
    we'll provide a helper class, which creates engine and sessionmaker
    on its instantiation and provides get_engine()/get_session() methods
    that are compatible with corresponding utility functions that currently
    exist in target projects, e.g. in Nova.

    engine/sessionmaker instances will still be global (and they are meant to
    be global), but they will be stored in the app context, rather that in the
    oslo.db context.

    Note: using of this helper is completely optional and you are encouraged to
    integrate engine/sessionmaker instances into your apps any way you like
    (e.g. one might want to bind a session to a request context). Two important
    things to remember:

    1. An Engine instance is effectively a pool of DB connections, so it's
       meant to be shared (and it's thread-safe).
    2. A Session instance is not meant to be shared and represents a DB
       transactional context (i.e. it's not thread-safe). sessionmaker is
       a factory of sessions.

    """

    def __init__(self, sql_connection, sqlite_fk=False, **kwargs):
        """Initialize engine and sessionmaker instances.

        :param sqlite_fk: enable foreign keys in SQLite
        :type sqlite_fk: bool

        :param autocommit: use autocommit mode for created Session instances
        :type autocommit: bool

        :param expire_on_commit: expire session objects on commit
        :type expire_on_commit: bool

        Keyword arguments:

        :keyword mysql_sql_mode: the SQL mode to be used for MySQL sessions.
                                 (defaults to TRADITIONAL)
        :keyword idle_timeout: timeout before idle sql connections are reaped
                               (defaults to 3600)
        :keyword connection_debug: verbosity of SQL debugging information.
                                   0=None, 100=Everything (defaults to 0)
        :keyword max_pool_size: maximum number of SQL connections to keep open
                                in a pool (defaults to SQLAlchemy settings)
        :keyword max_overflow: if set, use this value for max_overflow with
                               sqlalchemy (defaults to SQLAlchemy settings)
        :keyword pool_timeout: if set, use this value for pool_timeout with
                               sqlalchemy (defaults to SQLAlchemy settings)
        :keyword sqlite_synchronous: if True, SQLite uses synchronous mode
                                     (defaults to True)
        :keyword connection_trace: add python stack traces to SQL as comment
                                   strings (defaults to False)
        :keyword max_retries: maximum db connection retries during startup.
                              (setting -1 implies an infinite retry count)
                              (defaults to 10)
        :keyword retry_interval: interval between retries of opening a sql
                                 connection (defaults to 10)

        """

        super(EngineFacade, self).__init__()

        self._engine = create_engine(
            sql_connection=sql_connection,
            sqlite_fk=sqlite_fk,
            mysql_sql_mode=kwargs.get('mysql_sql_mode', 'TRADITIONAL'),
            idle_timeout=kwargs.get('idle_timeout', 3600),
            connection_debug=kwargs.get('connection_debug', 0),
            max_pool_size=kwargs.get('max_pool_size'),
            max_overflow=kwargs.get('max_overflow'),
            pool_timeout=kwargs.get('pool_timeout'),
            sqlite_synchronous=kwargs.get('sqlite_synchronous', True),
            connection_trace=kwargs.get('connection_trace', False),
            max_retries=kwargs.get('max_retries', 10),
            retry_interval=kwargs.get('retry_interval', 10),
            strategy=kwargs.get('strategy', 'plain'),
            executor=kwargs.get('executor', None),
            echo=kwargs.get('echo', False))

        self._session_maker = None

    def get_engine(self):
        """Get the engine instance (note, that it's shared)."""

        return self._engine

    def get_session_maker(self, autocommit=False, expire_on_commit=False, using_scope=False):
        if self._session_maker is not None:
            return self._session_maker

        session_maker = None
        try:
            session_maker = _get_maker(self._engine, autocommit=autocommit,
                                       expire_on_commit=expire_on_commit,
                                          using_scope=using_scope)
            return session_maker
        finally:
            self._session_maker = session_maker


    def get_session(self, autocommit=False, expire_on_commit=False, using_scope=False):
        """Get a Session instance.

        If passed, keyword arguments values override the ones used when the
        sessionmaker instance was created.

        :keyword autocommit: use autocommit mode for created Session instances
        :type autocommit: bool

        :keyword expire_on_commit: expire session objects on commit
        :type expire_on_commit: bool

        """
        return self.get_session_maker(autocommit=autocommit,
                                      expire_on_commit=expire_on_commit,
                                      using_scope=using_scope)()

    @classmethod
    def from_config(cls, connection_string, conf,
                    sqlite_fk=False, autocommit=True, expire_on_commit=False,
                    strategy='plain', executor=None):
        """Initialize EngineFacade using oslo.config config instance options.

        :param connection_string: SQLAlchemy connection string
        :type connection_string: string

        :param conf: oslo.config config instance
        :type conf: oslo.config.cfg.ConfigOpts

        :param sqlite_fk: enable foreign keys in SQLite
        :type sqlite_fk: bool

        :param autocommit: use autocommit mode for created Session instances
        :type autocommit: bool

        :param expire_on_commit: expire session objects on commit
        :type expire_on_commit: bool

        """
        engine_args = dict(conf.database.items())
        return cls(sql_connection=connection_string,
                   sqlite_fk=sqlite_fk,
                   strategy=strategy,
                   executor=executor,
                   **engine_args)


_FACADE = None


def _create_facade_lazily():
    global _FACADE

    if _FACADE is None:
        _FACADE = EngineFacade.from_config(
            cfg.CONF.database.connection, CONF, sqlite_fk=True)

    return _FACADE


def get_engine():
    """Helper method to grab engine."""
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session():
    """Helper method to grab session."""
    using_scope = CONF.portal.using_scope
    autocommit = CONF.portal.autocommit
    expire_on_commit = CONF.portal.expire_on_commit

    facade = _create_facade_lazily()
    return facade.get_session(autocommit=autocommit,
                              expire_on_commit=expire_on_commit,
                              using_scope=using_scope)


def get_session_maker():
    facade = _create_facade_lazily()
    return facade.get_session_maker()


@contextlib.contextmanager
def transactional(auto_close=True):
    """Provide a transactional scope around a series of operations."""
    using_scope = CONF.portal.using_scope

    session = get_session()
    try:
        yield session
        if not using_scope: session.commit()
    except:
        if not using_scope: session.rollback()
        raise
    finally:
        if auto_close and not using_scope:
            session.close()


if __name__ == '__main__':
    get_session()
