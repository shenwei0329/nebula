# -*- coding: utf-8 -*-

from .base import BaseManager
from nebula.core.models import Permission
from nebula.core.db import session as db_session


class PermissionManager(BaseManager):

    def create(self, name, view, method):
        with self.transactional() as session:
            permission = session.query(Permission).filter_by(view=view)\
                .first()
            if permission:
                return permission
            method = method.lower()
            permission = Permission(name=name,
                                    view=view,
                                    method=method)
            permission.save(session)
        return permission

    @classmethod
    def get_all(cls):
        with db_session.transactional() as session:
            permissions = session.query(Permission).all()
        return permissions

    @classmethod
    def get_by_exclude(cls, view_names):
        with db_session.transactional() as session:
            permissions = session.query(Permission).filter(Permission.view.notin_(view_names)).all()
        return permissions
