# -*- coding: utf-8 -*-
import logging

from six.moves import urllib

from functools import wraps

from flask import g
from flask import redirect
from flask import request
from flask import make_response
from flask import session
from flask import url_for

from nebula import version
from nebula.core import context as nebula_context

LOG = logging.getLogger(__name__)


def require_auth(func):

    @wraps(func)
    def decorated_view(*args, **kwargs):
        # 从 上下文 获取用户信息
        user = session.get('user', None)
        if user is not None:
            logging.warn(">>> decoreated_view: %s <<<" % user['username'])
        if not user or user is None:
            # 若用户未激活，则需要 注册
            url = url_for('portal.login')
            if '?' not in url:
                url += '?next=' + urllib.parse.quote_plus(request.url)
            """
            若没有用户信息，或用户无效，则重定向到 用户登陆 界面
            """
            return redirect(url)

        # 在请求的 上下文 中设置用户信息
        _set_request_context(user)
        # 返回
        return func(*args, **kwargs)
    return decorated_view


def require_permission(func):

    @wraps(func)
    def decorated_views(*args, **kwargs):
        return func(*args, **kwargs)

    return decorated_views


def _prefix_endpoint(end_point):
    return 'portal.{0}'.format(end_point)


def _set_request_context(user):
    kw = dict()
    logging.warn(">>> _set_request_context: %s:%s <<<" % (type(user), user['username']))
    g.context = nebula_context.RequestContext(user_id=None,
                                              is_super=False,
                                              user_name=user['username'],
                                              version=version,
                                              overwrite=True, **kw)
