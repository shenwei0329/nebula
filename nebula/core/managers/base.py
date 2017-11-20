# -*- coding: utf-8 -*-
import contextlib

import sqlalchemy.exc
from sqlalchemy.sql import column
from oslo_config import cfg

from nebula.core import context as context_utils
from nebula.core.db import session as db_session
#from nebula.core.mission import helpers as mission_helpers
from nebula.core.models import model_base
from nebula.openstack.common import log as logging
from nebula.core.i18n import _

LOG = logging.getLogger(__name__)
BASE = model_base.BASE
CONF = cfg.CONF
CONF.import_group('database', 'nebula.core.db.options')


def configure_db():
    """Configure database.

    Establish the database, create an engine if needed, and register
    the models.
    """
    #mission_helpers.configure_db()
    register_models()


def clear_db(base=BASE):
    unregister_models(base)
    #mission_helpers.clear_db()


def register_models(base=BASE):
    """Register Models and create properties."""
    try:
        with contextlib.closing(db_session.get_engine().connect()) as conn:
            base.metadata.create_all(conn)
    except sqlalchemy.exc.DBAPIError as e:
        LOG.error(_("Database registration exception: %s"), e)
        LOG.error(_("Statement: %s"), e.statement)
        return False
    return True


def unregister_models(base=BASE):
    """Unregister Models, useful clearing out data before testing."""
    try:
        with contextlib.closing(db_session.get_engine().connect()) as conn:
            base.metadata.drop_all(conn)
    except Exception as err:
        LOG.error(_("Database exception"))
        LOG.exception(err)


def dump_tables():
    result = []

    def dump(sql, *multiparams, **params):
        result.append(str(sql.compile(dialect=engine.dialect)))

    facade = db_session.EngineFacade.from_config(
        CONF.database.connection,
        CONF, sqlite_fk=True,
        strategy='mock',
        executor=dump)
    engine = facade.get_engine()
    BASE.metadata.create_all(engine, checkfirst=False)
    return '\n'.join(result)


class BaseManager(object):

    transactional = db_session.transactional

    @classmethod
    def model_query(cls, *args, **kwargs):
        """Query helper that accounts for context
        :param context: context to query under
        :param session: if present, the session to use
        :param user_only: Query specific user only
        :param args: session query arg
        """
        session = kwargs.get('session') or db_session.get_session()
        user_only = kwargs.get('user_only', True)

        # def issubclassof_nebula_base(obj):
        #     return (isinstance(obj, type) and
        #             issubclass(obj, model_base.NebulaBase))

        # base_model = model
        # if not issubclassof_nebula_base(base_model):
        #     base_model = kwargs.get('base_model', None)
        #     if not issubclassof_nebula_base(base_model):
        #         raise Exception(_("model or base_model parameter should be "
        #                           "subclass of NebulaBase"))

        query = model_base.BaseQuery(args, session)

        return query

    @classmethod
    def get_session(cls):
        return db_session.get_session()
