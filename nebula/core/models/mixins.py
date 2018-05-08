# -*- coding: utf-8 -*-
import logging

from flask import url_for
from werkzeug.routing import BuildError

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship

from nebula.core.common import nameutils

LOG = logging.getLogger(__name__)


class CreatorOwnerMixin(object):
    """
    Model用户关系Mixin.

    定义creator_id owner_id数据库字段, 与ORM Object属性creator owner
    """
    @declared_attr
    def creator_id(cls):
        return Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))

    @declared_attr
    def owner_id(cls):
        return Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))

    @declared_attr
    def creator(cls):
        return relationship('User',
                            lazy='joined',
                            backref=backref('creator_%s' % cls.__tablename__),
                            primaryjoin='User.id == %s.creator_id' %
                                        cls.__name__)

    @declared_attr
    def owner(cls):
        return relationship('User',
                            lazy='joined',
                            primaryjoin='User.id == %s.owner_id' %
                                        cls.__name__)


class HasJobMixin(object):
    @declared_attr
    def job_id(cls):
        return Column(Integer, ForeignKey('jobs.id', ondelete='SET NULL'))

    @declared_attr
    def job(cls):
        singular_name = nameutils.snake_casify(cls.__name__)
        return relationship('Job',
                            uselist=False,
                            backref=backref(singular_name),
                            primaryjoin='Job.id == %s.job_id' % cls.__name__)

    # def get_jobs(self):
    #     session = get_session()
    #     with session.begin():
    #         return session.query(Job).filter_by(resource_id=self.id,
    #                                             resource_type=self.__class__.name).all()


class URLMixin(object):

    @classmethod
    def get_access_url(cls, id):
        try:
            return url_for(cls._get_bp_endpoint(), id=id)
        except BuildError as ex:
            LOG.warning('build url error: %s', ex)

    @classmethod
    def _get_bp_endpoint(cls):
        return '{blueprint_name}.{endpoint}'.format(
            blueprint_name=cls._get_blueprint_name(),
            endpoint=cls._get_endpoint(),
        )

    @classmethod
    def _get_endpoint(cls):
        return '{class_name}_detail'.format(class_name=nameutils.snake_casify(
            cls.__name__
        ))

    @classmethod
    def _get_blueprint_name(cls):
        return 'portal'
