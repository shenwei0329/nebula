# -*- coding: utf-8 -*-
import copy

import six

def generate_request_id():
    return 'req-'


class RequestContext(object):
    """
    Business context.

    保存与业务相关的常用属性, 如 user_id 等.

    获得RequestContext的实例后, 可按一下方式访问常用变量::

        context.user_id     # 当前登录的用户ID
        context.user_name   # 当前登录的用户名称
        context.is_super    # 是否是管理员
        context.roles       # 当前登录用户的角色
    """
    def __init__(self, user_id, is_super=False, user_name=None, roles=None,
                 timestamp=None, request_id=None, overwrite=True, **kwargs):
        """
           :param overwrite: Set to False to ensure that the greenthread local
                copy of the index is not overwritten.

           :param kwargs: Extra arguments that might be present, but we ignore
                because they possibly came in from older rpc messages.
        """
        self.user_id = user_id
        self.is_super = is_super
        self.user_name = user_name
        self.roles = roles or []

        self.timestamp = timestamp
        if not request_id:
            request_id = generate_request_id()
        self.request_id = request_id

        if kwargs and 'permissions' in kwargs:
            self.permissions = kwargs.get('permissions')

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'is_super': self.is_super,
            'roles': self.roles,
            'request_id': self.request_id,
        }

    @classmethod
    def from_dict(cls, values):
        return cls(**values)

    def elevated(self):
        """Return a version of this context with admin flag set."""
        context = copy.copy(self)
        context.is_super = True

        if 'admin' not in context.roles:
            context.roles.append('admin')
        return context


def get_admin_context():
    return RequestContext(user_id=None, is_super=True, overwrite=False)


def is_user_context(context):
    """Indicates if the request context is a normal user."""
    if not context:
        return False
    if context.is_super:
        return False
    if not context.user_id:
        return False
    return True
