# -*- coding: utf-8 -*-
import time
from sqlalchemy.sql import func
from sqlalchemy.sql import column

from nebula.core import constants
from nebula.core.managers.base import BaseManager
from nebula.core.models import Volume
from nebula.core.context import is_user_context

class VolumeManager(BaseManager):

    def _get(self, context, volume_id, session=None):
        return self.model_query(context, Volume, session=session, user_only=False).\
            filter_by(id=volume_id).first()

    def get(self, context, volume_id):
        return self._get(context, volume_id)

    def get_by(self, context, session=None, **kwargs):
        return self.model_query(context, Volume,
                                session=session, user_only=False).filter_by(**kwargs).first()

    def create(self, user_id, **kwargs):
        volume_uuid = None
        if kwargs.get("volume_uuid", None):
            volume_uuid = kwargs["volume_uuid"]
        if kwargs.get("cinder_types", None):
            cinder_types = kwargs["cinder_types"]
        with self.transactional() as session:
            volume = Volume(
                volume_uuid=volume_uuid,
                name=kwargs["name"],
                description=kwargs.get("description", None),
                size=kwargs["size"],
                status=constants.VOLUME_CREATING,
                cinder_types=cinder_types,
                creator_id=user_id,
                owner_id=user_id)
            volume.save(session)
        return volume

    def update(self, context, volume_id, **values):
        with self.transactional() as session:
            volume = self._get(context, volume_id, session)
            volume.update(values)
        return volume

    def update_by_uuid(self, context, volume_uuid, **values):
        retry = 5
        with self.transactional() as session:
            volume = self.get_by(context, session, volume_uuid=volume_uuid)
            i = 0
            while not volume:
                if i >= retry:
                    break
                i += 1
                time.sleep(2)
                volume = self.get_by(context, session, volume_uuid=volume_uuid)
            volume.update(values)
            volume.save(session)
        return volume

    def delete_by(self, **kwargs):
        with self.transactional() as session:
            session.query(Volume).filter_by(**kwargs).delete()

    def list(self):
        with self.transactional() as session:
            return session.query(Volume).filter_by()
    
    def avail_list_by_user(self, user_id):
        with self.transactional() as session:
            return session.query(Volume).filter_by(status="available",
                                                   owner_id=user_id).all()

    def avail_list_by_user_and_type(self, cinder_type, user_id):
        with self.transactional() as session:
            return session.query(Volume).filter_by(status="available",
                                                   cinder_types=cinder_type,
                                                   owner_id=user_id).all()
    def avail_list_by_user_and_notype(self, cinder_type, user_id):
        with self.transactional() as session:
            return session.query(Volume).filter(Volume.status=="available",
                                                   Volume.cinder_types!=cinder_type,
                                                   Volume.owner_id==user_id).all()

    def inuse_list_by_instance(self, instance_id):
        with self.transactional() as session:
            return session.query(Volume).\
                filter_by(status="in-use", instance_id=instance_id).all()

    def count_all_size(self):
        with self.transactional() as session:
             result = session.query(func.sum(Volume.size)).filter(~Volume.status.in_([constants.VOLUME_CREATING, 
                                                                                      constants.VOLUME_DELETING,
                                                                                      constants.VOLUME_DELETED])).scalar() 
        return result or 0

    def get_backups_count(self, context, **kwargs):
        volume_id = kwargs.get('volume_id')
        with self.transactional() as session:
            volume = session.query(Volume)\
                .filter(Volume.id == volume_id,
                        owner_id=context.user_id).first()
            if volume:
                return len(volume.backups)
        return -1

    def availables(self, context, is_oneself=False, **kwargs):
        return self.image_query(context, is_oneself=is_oneself, **kwargs).\
            filter(column('status') == 'available').all()
            
#iso创建虚机需去除掉vmdk的卷
    def availables_notype(self, context, cinder_type, is_oneself=False, **kwargs):
        return self.image_query(context, is_oneself=is_oneself, **kwargs).\
            filter(column('status') == 'available', column('cinder_types')!=cinder_type).all()
                   
    def image_query(self, context, is_oneself=False, **kwargs):
        query = self.model_query(context, Volume, user_only=False)
        if is_oneself:
            if is_user_context(context):
                query = query.filter_by(owner_id=context.user_id)
            else:
                query = query.filter(column('owner_id') != None)
        else:
            query = query.filter_by(owner_id=None)
        return query