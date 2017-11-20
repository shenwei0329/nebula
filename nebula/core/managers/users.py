# -*- coding: utf-8 -*-

import copy
import logging

from sqlalchemy import exc
from werkzeug.security import generate_password_hash

from nebula.core.models import User
from nebula.core.models import UserRole
from nebula.core.models import UserLogin
from nebula.core.models import Quota
from nebula.core.models import Permission
from nebula.core.models import RolePermission
from nebula.core.managers.base import BaseManager
from nebula.core.db import session as db_session
from .utils import Transfer

LOG = logging.getLogger(__name__)


class UserManager(BaseManager):

    def get(self, id):
        with self.transactional() as session:
            return session.query(User).get(id)

    def create(self, username, password, is_super=False, region=None):
        with self.transactional() as session:
            user = session.query(User).filter_by(username=username).first()
            if user:
                return None
            password = generate_password_hash(password)
            user = User(username=username,
                        password=password,
                        is_super=is_super,
                        region=region)
            user.save(session)
        return user

    def get_all(self, context):
        return self.model_query(context, User).all()

    def get_by_username(self, username):
        with db_session.transactional() as session:
            data = session.query(User).filter(User.username == username,
                                              User.deleted == False).first()
        return data if data else None

    @classmethod
    def new(cls, **kwargs):
        """
        Create(New) User by User Interface
        Return True when success.
        """
        transfer = Transfer()
        if 'username' not in kwargs.keys():
            transfer.error(message=u'not username field')
            return transfer
        with db_session.transactional() as session:
            user = cls.get_by_username(kwargs['username'])
            if user:
                transfer.error(message=u'user exist.')
                return transfer
            try:
                roles = kwargs.pop('roles')
                quotas = kwargs.pop('quotas')
                kwargs["password"] = generate_password_hash(kwargs["password"])
                user = User(**kwargs)
                user.save(session)
                # create user's role
                cls.set_roles(session=session,
                              user_id=user.id,
                              roles=roles)
                # create user's quota
                cls._create_user_quota(session, user.id, **quotas)
                transfer.record(user)
                return transfer
            except Exception as ex:
                LOG.error('create user error: %s' % ex)
                transfer.error(message=ex)
                return transfer

    @classmethod
    def _create_user_quota(cls, session, user_id, **kwargs):
        quotas = session.query(Quota).filter_by(user_id=user_id).all()
        resources = [quota.resource for quota in quotas]
        resource_list = copy.copy(kwargs)
        for item in resource_list.iteritems():
            if item[0] in resources:
                continue
            quota = Quota(user_id=user_id,
                          resource=item[0],
                          hard_limit=item[1])
            quota.save(session)

    @classmethod
    def _get_user_by_id(cls, session, user_id):
        return session.query(User).filter_by(id=user_id,
                                             deleted=False).first()

    @classmethod
    def get_by_username(cls, username):
        with db_session.transactional() as session:
            user = session.query(User).filter_by(username=username,
                                                 deleted=False).first()
        return user

    @classmethod
    def get_by_id(cls, user_id):
        with db_session.transactional() as session:
            user = session.query(User).filter_by(id=user_id,
                                                 deleted=False).first()
        return user

    @classmethod
    def last_login(cls, request, user_id):
        with db_session.transactional() as session:
            user = cls._get_user_by_id(session, user_id)
            if not user:
                LOG.error("Update user's last login not found user ")
                return
            user.update_last_login()
            user.save(session)
            user_login = UserLogin(user_id=user.id,
                                   ip=request.remote_addr)
            user_login.save(session)

    @classmethod
    def delete(cls, user_id):
        with db_session.transactional() as session:
            transfer = Transfer()
            user = cls._get_user_by_id(session, user_id)
            if not user:
                transfer.error(message=u'not found the user.')
                return transfer
            user.deleted = True
            user.save(session)
        return transfer

    @classmethod
    def change_password(cls, user_id, password):
        with db_session.transactional() as session:
            user = cls._get_user_by_id(session, user_id)
            if not user:
                return False
            user.change_password(password)
            user.save(session)
        return True

    @classmethod
    def set_roles(cls, session=None, user_id=None, roles=None):
        transfer = Transfer()
        LOG.info("start: set user's roles: user_id(%s),roles(%s)" % ( user_id,
                 roles))
        if not session:
            session = db_session.get_session()
        if not roles:
            roles = []
        try:
            user_roles = session.query(UserRole).\
                filter(UserRole.user_id == user_id).all()
            user_roles = [item.role_id for item in user_roles]

            # find & remove roles
            _need_rm_roles = [item for item in user_roles
                              if item not in roles]
            if _need_rm_roles:
                _need_rm_roles = session.query(UserRole).\
                    filter(UserRole.user_id == user_id,
                           UserRole.role_id.in_(_need_rm_roles)).all()
                for item in _need_rm_roles:
                    session.delete(item)
            # find & add roles
            _need_add_roles = [item for item in roles
                               if item not in user_roles]
            for item in _need_add_roles:
                user_role = UserRole(user_id=user_id, role_id=item)
                session.add(user_role)
        except Exception as ex:
            LOG.error("Set user's roles error: %s" % ex)
            transfer.error(message=ex.message)
        return transfer

    @classmethod
    def find_duplicate_username(cls, user_id, username):
        with db_session.transactional() as session:
            user = session.query(User).filter(User.username == username,
                                              User.id != user_id).first()
        return True if user else False

    @classmethod
    def update(cls, **kwargs):
        transfer = Transfer()
        with db_session.transactional() as session:
            user = cls._get_user_by_id(session, kwargs['user_id'])
            if not user:
                transfer.error(message=u'Not found the user')
                return transfer
            try:
                if 'username' in kwargs.keys() and kwargs.get('username'):
                    user.username = kwargs['username']
                if 'status' in kwargs.keys():
                    user.active = kwargs['status']
                user.email = kwargs['email']
                user.phone = kwargs['phone']
                user.save(session)
                return transfer
            except Exception as ex:
                LOG.error("update user failure: %s " % ex)
                transfer.error(message=ex)
                return transfer

    @classmethod
    def update_status(cls, user_id, status):
        with db_session.transactional() as session:
            user = cls._get_user_by_id(session, user_id)
            if not user:
                return False
            user.active = status
            user.save(session)
        return True

    @classmethod
    def get_all_by_active(cls):
        with db_session.transactional() as session:
            users = session.query(User).filter(User.active==True,
                                               User.is_super == False,
                                               User.deleted == False).all()
        return users

    @classmethod
    def get_all_query(cls, context):
        query = User.query.filter(User.deleted == False)
        return query

    @classmethod
    def get_logs(cls, user_id, is_super=False, limit=5):
        with db_session.transactional() as session:
            query = session.query(UserLogin)
            if not is_super:
                query = query.filter(UserLogin.user_id==user_id)
            result = query.join(UserLogin.user)\
                .order_by('-user_login.id')\
                .limit(limit)
        return result

    @classmethod
    def get_permissions_by_user(cls, user_id):
        """
        Get permissions by User
        :param user_id:
        :return: permissions
        """
        permissions = dict()
        with db_session.transactional() as session:
            user = session.query(User).filter(User.id == user_id,
                                              User.active == True,
                                              User.deleted == False).first()
            if not user:
                return permissions
            user_roles = session.query(UserRole).\
                filter(UserRole.user_id == user.id).all()
            roles = [role.role_id for role in user_roles if role.role.active]


            permissions_query = session.query(Permission).\
                join(RolePermission,
                     Permission.id == RolePermission.permission_id).filter(
                RolePermission.role_id.in_(roles)
            ).all()
            for permission in permissions_query:
                if permission.view not in permissions:
                    permissions.update({
                        permission.view:dict(
                            method=permission.method,
                        )
                    })
        return permissions



