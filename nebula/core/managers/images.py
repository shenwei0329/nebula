# -*- coding: utf-8 -*-

import logging

from nebula.core import constants
from nebula.core import models, Image
from sqlalchemy.sql import column

from nebula.core.context import is_user_context

from .base import BaseManager
from nebula.core.managers import cache
import math

LOG = logging.getLogger(__name__)


class ImageManager(cache.CountCacheMixin, BaseManager):
    
    def _get_by(self, context, session=None, **values):
        if not session:
            session = self.get_session()
        return self.model_query(context, models.Image, session=session, user_only=False) \
                   .filter_by(**values) \
                   .first()

    def get_by(self, context, **values):
        return self._get_by(context, **values)

    def get(self, context, resource_id, session=None):
        return self.model_query(context, Image, session=session, user_only=False).get(resource_id)

    def delete(self, context, image):
        with self.transactional() as session:
            if isinstance(image, (int, long)):
                image = session.query(models.Image).get(image)
            session.delete(image)

    def update(self, context, **kwargs):
        LOG.info("update_1:::::")
        LOG.info(kwargs)
        resource_id = kwargs.pop('resource_id')
        with self.transactional() as session:
            image = self.get(context, resource_id, session)
        
            LOG.info("update_2:::::")
            image.update(kwargs)
            image.save(session)
            LOG.info("update_4:::::")

        return image
                   
    def _delete_by(self, context, values, session=None):
        with self.transactional() as session:
            self.model_query(context, models.Image, session=session, user_only=False) \
                .filter_by(**values) \
                .delete()

    def delete_by(self, context, values):
        return self._delete_by(context, values)
    
    def update_by_uuid(self, context, uuid, values):
        with self.transactional() as session:
            # Find image by image's uuid
            image_ref = session.query(models.Image).\
                filter_by(image_uuid=uuid).first()
            if image_ref:
                image_ref.update(values)
                image_ref.save(session)
        return image_ref

    def update_by_id(self, context, id, values):
        with self.transactional() as session:
            image_ref = self._get_by(context, session=session, id=id)
            image_ref.update(values)
            image_ref.save(session)
        return image_ref

    def create(self, creator_id, **kwargs):
        with self.transactional() as session:
            image = Image(
                name=kwargs.get("name"),
                disk_format=kwargs.get("disk_format"),
                container_format=kwargs.get("container_format"),
                size=kwargs.get("size"),
                status=constants.IMAGE_STATUS_QUEUED,
                is_public = True,
                min_disk =1+math.ceil(int(kwargs.get("min_disk"))/1024.0/1024/1024*100)/100,
                min_ram = 0,
                architecture = kwargs.get("architecture"),
                os_distro = kwargs.get("os_type"),
                creator_id=creator_id,
                owner_id=creator_id
            )
            image.save(session)
            return image

    def create_by_image_uuid(self, context, image_uuid, **values):
        LOG.info("get_by_1:::::::::::")
        LOG.info(values)
        with self.transactional() as session:
            image_ref = session.query(models.Image).\
                filter_by(image_uuid=image_uuid).first()
            if not image_ref:
                image_ref = models.Image(image_uuid=image_uuid)
            values['image_uuid'] = image_uuid
            image_ref.update(values)
            image_ref.save(session)
            return image_ref

    def all(self, context, is_oneself=False, **kwargs):
        return self.image_query(context, is_oneself=is_oneself, **kwargs).all()

    def availables(self, context, is_oneself=False, **kwargs):
        return self.image_query(context, is_oneself=is_oneself, **kwargs).\
            filter(column('image_uuid') != None,
                   column('status') != 'deleted',
                   column('status') != 'saving',
                   column('status') != 'queued').all()

    def image_query(self, context, is_oneself=False, **kwargs):
        query = self.model_query(context, models.Image, user_only=False)
        if is_oneself:
            if is_user_context(context):
                query = query.filter_by(owner_id=context.user_id)
            else:
                query = query.filter(column('owner_id') != None)
        else:
            query = query.filter_by(owner_id=None)
        return query

    def count_all(self):
        with self.transactional() as session:
            result = session.query(Image).filter(Image.status == 'active').count()
            return result or 0
