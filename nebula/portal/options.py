# -*- coding: utf-8 -*-
from oslo_config import cfg

from nebula.core import constants

CONF = cfg.CONF

portal_opts = [
    # Flask options
    cfg.BoolOpt('DEBUG',
                default=True,
                help="enable/disable debug mode"),
    cfg.BoolOpt('TESTING',
                default=False,
                help="enable/disable testing mode"),
    cfg.StrOpt('SECRET_KEY',
               default='development key',
               help="the secret key"),
    cfg.StrOpt('SESSION_COOKIE_NAME',
               default='session',
               help="the name of the session cookie"),
    cfg.StrOpt('SESSION_COOKIE_DOMAIN',
               default=None,
               help="the domain for the session cookie. If this is not set, "
                    "the cookie will be valid for all subdomains of "
                    "SERVER_NAME."),
    cfg.StrOpt('SESSION_COOKIE_PATH',
               default=None,
               help="the path for the session cookie. If this is not set the "
                    "cookie will be valid for all of APPLICATION_ROOT or if "
                    "that is not set for '/'."),
    cfg.BoolOpt('SESSION_COOKIE_HTTPONLY',
                default=True,
                help="controls if the cookie should be set with the httponly "
                     "flag. Defaults to True."),
    cfg.BoolOpt('SESSION_COOKIE_SECURE',
                default=False,
                help="controls if the cookie should be set with the secure "
                     "flag. Defaults to False."),
    cfg.BoolOpt('TRAP_BAD_REQUEST_ERRORS',
                default=False),
    cfg.BoolOpt('TRAP_HTTP_EXCEPTIONS',
                default=False),
    cfg.BoolOpt('JSON_AS_ASCII',
                default=False,
                help="By default Flask serialize object to ascii-encoded JSON. "
                     "If this is set to False Flask will not encode to ASCII "
                     "and output strings as-is and return unicode strings. "
                     "jsonify will automatically encode it in utf-8 then for "
                     "transport for instance."),
    cfg.BoolOpt('JSON_SORT_KEYS',
                default=False),
    cfg.BoolOpt('JSONIFY_PRETTYPRINT_REGULAR',
                default=True,
                help="If this is set to True (the default) jsonify responses "
                     "will be pretty printed if they are not requested by an "
                     "XMLHttpRequest object (controlled by the X-Requested-With "
                     "header)"),

    # Debug toolbar options
    cfg.BoolOpt('DEBUG_TB_INTERCEPT_REDIRECTS',
                default=False,
                help='Set Toolbar redirect confirm page.'),
    cfg.BoolOpt('DEBUG_TB_PROFILER_ENABLED',
                default=False),

    # Custom options
    cfg.BoolOpt('WTF_CSRF_ENABLED',
                default=False,
                help="whether to use CSRF protection. If False, all "
                     "csrf behavior is suppressed. "
                     "Default: WTF_CSRF_ENABLED config value"),
    cfg.IntOpt('DEFAULT_PER_PAGE',
               default=5,
               help="Default each page record count"),
    cfg.StrOpt('REDIS_HOST',
               default='127.0.0.1',
               help="redis host"),
    cfg.IntOpt('REDIS_PORT',
               default=6379,
               help="redis port"),
    cfg.IntOpt('REDIS_DB',
               default=0,
               help="redis port"),
    cfg.StrOpt('REDIS_PASSWORD',
               default=None,
               help="redis password"),
    cfg.IntOpt('DEFAULT_KEY_EXPIRE',
               default=60 * 60 * 24 * 3,
               help="redis key expire time. default is three days"),
    cfg.StrOpt('BABEL_DEFAULT_LOCALE',
               default=constants.DEFAULT_LOCALE,
               help="The default locale to use if no locale selector is registered. "
                    "This defaults to 'en'."),
    cfg.StrOpt('BABEL_DEFAULT_TIMEZONE',
               default=constants.DEFAULT_TIMEZONE,
               help="The timezone to use for user facing dates. "
                    "This defaults to 'UTC' which also is the timezone your "
                    "application must use internally."),
    cfg.BoolOpt('autocommit',
                default=False,
                help='Auto commit to database'),
    cfg.BoolOpt('using_scope',
                default=False,
                help='using_scope'),
    cfg.BoolOpt('expire_on_commit',
                default=False,
                help='expire_on_commit'),
]

CONF.register_opts(portal_opts, group='portal')

webapp_opts = [

    #
    # shenwei.
    #
    cfg.StrOpt('ldap_server_host',
               default='10.0.1.60',
               help="LDAP server address"),

    cfg.StrOpt('ldap_user',
               default='cn=Manager,dc=yun70,dc=com',
               help="The name of LDAP manager"),

    cfg.StrOpt('ldap_passwd',
               default='sw64419',
               help="The password of LDAP manager"),

    cfg.StrOpt('rest_api_register',
               default='http://localhost:8787/get_url',
               help="REST api Register URL"),

    cfg.StrOpt('rest_api_register_web',
               default='http://localhost:8787/admin',
               help="REST api Register URL"),

]

CONF.register_opts(webapp_opts, group='webapp')

portal_cli_opts = [
        cfg.StrOpt('address',
                   default='0.0.0.0',
                   help='RESTful API server bind address'),
        cfg.IntOpt('port',
                   default=8000,
                   help='RESTful API server port'),
    ]
CONF.register_cli_opts(portal_cli_opts, group='portal')
