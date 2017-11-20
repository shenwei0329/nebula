# -*- coding: utf-8 -*-
"""
    2015.7.12 by shenwei @ChengDu

    2017.7.12：对文档进行注释。

"""
import six
from flask import Flask, request
from flask_babel import Babel
from flask_debugtoolbar import DebugToolbarExtension
from oslo_config import cfg

from nebula.core import config
from nebula.core.db import session as db_session
from nebula.core.i18n import _
from nebula.core.cache import get_cache

from views.portal import portal_bp
from flask.ext.bootstrap import Bootstrap
from flask.ext.admin import Admin

#from nebula.utils.tools.ldap_api import LDAP

from . import jinja_ext

app = Flask(__name__)

# 导入配置
CONF = cfg.CONF
CONF.import_group('portal', 'nebula.portal.options')

class FlaskConfigObject(object):
    @classmethod
    def from_dict(cls, dict_options):
        o = cls()
        for k, v in six.iteritems(dict_options):
            k = k.upper()
            setattr(o, k, v)
        return o


def _setup_opts():
    # Setup configuration
    config.set_defaults(prog='nebula-portal')
    config.setup_logging()

    CONF.portal.using_scope = True

def create_app(setup_config=True):

    if setup_config:
        _setup_opts()

    app = Flask(__name__)
    # Load flask configuration
    app.config.from_object(FlaskConfigObject.from_dict(
        dict(CONF.portal.items())))

    @app.before_request
    def setup_config():
        CONF.portal.using_scope = True

    # register request sesison handler
    if CONF.portal.using_scope:
        @app.teardown_appcontext
        def shutdown_session(response_or_exc):
            if response_or_exc is None:
                db_session.get_session().commit()
            db_session.get_session_maker().remove()
            return response_or_exc

    jinja_ext.register_functions(app)
    jinja_ext.register_filters(app)

    # register blueprint
    # 注册 蓝本
    #
    app.register_blueprint(portal_bp)

    # register babel
    # 注册 本地化引擎
    #
    babel = Babel(app)
    bootstrap=Bootstrap(app)
    admin = Admin(app)

    @babel.localeselector
    def get_locale():
        """
        根据浏览器语言选择i18n locale.
        """
        #TODO(xuwenbao): 根据用户自己配置的语言, 选择i18n locale
        return request.accept_languages.best_match(['zh', 'en'])

    # register toolbar
    #DebugToolbarExtension(app)

    # Cache
    app.redis = get_cache()

    return app

@app.route('/_add_numbers')
def add_numbers():
    return jsonify(result=5)
    #return ETLToolsView.add_numbers()

