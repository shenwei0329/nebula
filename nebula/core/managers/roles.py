# -*- coding: utf-8 -*-
import logging

from nebula.core.models import User
from nebula.core.models import Role
from nebula.core.models import UserRole
from nebula.core.models import RolePermission
from nebula.core.models import Permission
from nebula.core.db import session as db_session
from .base import BaseManager
from .utils import Transfer

LOG = logging.getLogger(__name__)


class RoleManager(BaseManager):

    @classmethod
    def create(cls, name, permissions, users):
        """
        Create Role
        """
        transfer = Transfer()
        with db_session.transactional() as session:
            role = session.query(Role).filter_by(name=name).first()
            if role:
                transfer.error(message=u'role name exist.')
                return transfer
            try:
                role = Role(name=name)
                role.save(session)
                # filter permission
                permissions = session.query(Permission).\
                    filter(Permission.id.in_(permissions)).all()
                # add role permission relationship
                for permission in permissions:
                    role_permission = RolePermission(role_id=role.id,
                                                     permission_id=permission.id)
                    role_permission.save(session)

                # filter active user
                if users:
                    users = session.query(User).filter(User.id.in_(users),
                                                       User.active).all()
                    # add user role relationship
                    for user in users:
                        user_role = UserRole(role_id=role.id,
                                             user_id=user.id)
                        user_role.save(session)
                return transfer
            except Exception as ex:
                LOG.error('Create role Error: %s' % ex)
                transfer.error(message=ex.message)
                return transfer

    @classmethod
    def delete(cls, role_id):
        """
        Delete Role by Role's id.
        """
        transfer = Transfer()
        with db_session.transactional() as session:
            role = session.query(Role).filter_by(id=role_id).first()
            if not role:
                transfer.error(message=u'not found role when deleted.')
                LOG.error('Not found role when deleted: role id:%s' % role_id)
                return transfer
            try:
                session.delete(role)
            except Exception as ex:
                transfer.error(message=ex.message)
        return transfer

    @classmethod
    def get_all_by_active(cls):
        with db_session.transactional() as session:
            roles = session.query(Role).filter_by(active=True)
        return roles

    @classmethod
    def get_all_by_user(cls, user_id):
        with db_session.transactional() as session:
            roles = session.query(Role).filter_by(active=True)
            user_roles = session.query(UserRole).\
                filter(UserRole.user_id == user_id).all()
            user_roles = [item.role_id for item in user_roles]
            role_list = []
            for role in roles:
                item = {
                    'id': role.id,
                    'name': role.name,
                    'select': False,
                }
                if role.id in user_roles:
                    item['select'] = True
                role_list.append(item)
        return role_list

    @classmethod
    def get_users(cls, role_id):
        with db_session.transactional() as session:
            users = session.query(User).filter_by(active=True,
                                                  is_super=False,
                                                  deleted=False).all()
            user_roles = session.query(UserRole).\
                filter(UserRole.role_id == role_id).all()
            user_roles = [item.user_id for item in user_roles]
            res = []
            for user in users:
                item = {
                    'id': user.id,
                    'username': user.username,
                    'selected': False
                }
                if user.id in user_roles:
                    item.update({
                        'selected': True
                    })
                res.append(item)
        return res

    @classmethod
    def get_permissions(cls, role_id):
        with db_session.transactional() as session:
            permissions = session.query(Permission).all()
            role_permissions = session.query(RolePermission).\
                filter(RolePermission.role_id == role_id).all()
            role_permissions = [item.permission_id for item in role_permissions]
            res = []
            for permission in permissions:
                item = {
                    'id': permission.id,
                    'name': permission.name,
                    'selected': False
                }
                if permission.id in role_permissions:
                    item.update({
                        'selected': True
                    })
                res.append(item)
        return res

    @classmethod
    def get(cls, role_id):
        with db_session.transactional() as session:
            role = session.query(Role).filter(Role.id == role_id).first()
        return role

    @classmethod
    def update_permissions(cls, role_id, permissions):
        transfer = Transfer()
        with db_session.transactional() as session:
            role_permissions = session.query(RolePermission).filter(
                RolePermission.role_id == role_id).all()
            role_permissions = [item.permission_id for item in role_permissions]
            # find & remove permissions
            _need_rm_permissions = [item for item in role_permissions
                                    if item not in permissions]
            _need_rm_permissions = session.query(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id.in_(_need_rm_permissions)
            ).all()

            for item in _need_rm_permissions:
                session.delete(item)
            # find & add permissions
            _need_add_permissions = [item for item in permissions
                                     if item not in role_permissions]

            for item in _need_add_permissions:
                role_permission = RolePermission(role_id=role_id,
                                                 permission_id=item)
                session.add(role_permission)
        return transfer

    @classmethod
    def update_users(cls, role_id, users):
        transfer = Transfer()

        if not users:
            users = []
        try:
            with db_session.transactional() as session:
                user_roles = session.query(UserRole).filter(
                    UserRole.role_id == role_id).all()
                user_roles = [item.user_id for item in user_roles]
                # find & remove users
                _need_rm_users = [item for item in user_roles
                                  if item not in users]
                _need_rm_users = session.query(UserRole).filter(
                    UserRole.role_id == role_id,
                    UserRole.user_id.in_(_need_rm_users)
                )
                for item in _need_rm_users:
                    session.delete(item)
                # find & add users
                _need_add_users = [item for item in users
                                   if item not in user_roles]
                for item in _need_add_users:
                    user_role = UserRole(role_id=role_id,
                                         user_id=item)
                    session.add(user_role)
        except Exception as ex:
            LOG.error("update role to user relationship error:%s" % ex)
            transfer.error(message=ex.message)
        return transfer

    @classmethod
    def update(cls, role_id, **kwargs):
        transfer = Transfer()
        with db_session.transactional() as session:
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                transfer.error(message=u'Not found the role.')
                return transfer
            if 'name' in kwargs.keys():
                roles = session.query(Role).\
                    filter(Role.id != role_id,
                           Role.name == kwargs['name']).all()
                if roles:
                    LOG.error("the name can not use.")
                    transfer.error(message=u'the role name can not use.')
                    return transfer
            role.name = kwargs['name']
            role.active = kwargs['active']
            role.save(session)
        return transfer
