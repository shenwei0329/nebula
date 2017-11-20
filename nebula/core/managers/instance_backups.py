# -*- coding: utf-8 -*-

from sqlalchemy.sql import func

from nebula.core import models

from .base import BaseManager
import logging 
LOG = logging.getLogger(__name__)


class InstanceBackupManager(BaseManager):
    def _get(self, context, id, session=None):
        if not session:
            session = self.get_session()
        return self.model_query(context,
                                models.InstanceBackup,
                                session=session, user_only=False).get(id)

    def get(self, context, id):
        return self._get(context, id)

    def get_by(self, context, **kwargs):
        return self.model_query(context, models.InstanceBackup) \
                   .filter_by(**kwargs) \
                   .first()

    def _get_by_uuid(self, context, backup_uuid, session=None):
        if not session:
            session = self.get_session()
        return self.model_query(context,
                                models.InstanceBackup,
                                session=session)\
            .filter_by(backup_uuid=backup_uuid).first()

    def get_by_uuid(self, context, backup_uuid):
        return self._get_by_uuid(context, backup_uuid)

    def create(self, context, **kwargs):
        with self.transactional() as session:
            instance = models.InstanceBackup(**kwargs)
            session.add(instance)
        return instance

    def _delete_by(self, context, values, session=None):
        with self.transactional() as session:
            self.model_query(context,
                             models.InstanceBackup,
                             session=session, user_only=False)\
                .filter_by(**values) \
                .delete()

    def delete_by(self, context, values):
        return self._delete_by(context, values)

    def delete_by_id(self, context, id):
        return self._delete_by(context, dict(id=id))

    def delete_by_uuid(self, context, backup_uuid):
        LOG.info("delete_by_uuid_1::::")
        LOG.info(backup_uuid)
        return self._delete_by(context, dict(backup_uuid=backup_uuid))

    def update(self, context, instance_id, values):
        with self.transactional() as session:
            instance = self._get(context, instance_id, session=session)
            instance.update(values)
        return instance

    def update_by_uuid(self, context, instance_uuid, values):
        with self.transactional() as session:
            instance_ref = self.update(context,
                                       instance_uuid,
                                       session=session)
            instance_ref.update(values)
            instance_ref.save(session)
        return instance_ref

    def update_by_id(self, context, id, values):
        with self.transactional() as session:
            instance_ref = self._get(context, id, session=session)
            instance_ref.update(values)
            instance_ref.save(session)
        return instance_ref
        
    def create_by_instance_backup_uuid(self, context, instance_uuid, **values):
        backup_uuid = values.get('backup_uuid')
        with self.transactional() as session:
            backup_ref = session.query(models.InstanceBackup).\
                filter_by(backup_uuid=backup_uuid).first()
            if not backup_ref:
                backup_ref = models.InstanceBackup(backup_uuid=backup_uuid)
            instance_info = session.query(models.Instance).\
                filter_by(instance_uuid=instance_uuid).first()
            # LOG.info("create_by_instance_backup_uuid @@@@@@@@@@@@ creator_id: %s <<<<" % context.user_id)
            if instance_info:
                values.update({
                    'creator_id': context.user_id,
                    'owner_id': instance_info.owner_id,
                    'instance_id': instance_info.id,
                    'size': 0
                })
            backup_ref.update(values)
            backup_ref.save(session)
        return backup_ref
    
    def update_by_backup_uuid(self, context, backup_uuid, values):
        with self.transactional() as session:
            instance_ref = self._get_by_uuid(context, backup_uuid, session)
            if instance_ref:
                instance_ref.update(values)
                instance_ref.save(session)
        return instance_ref

    def sum_disk(self):
        with self.transactional() as session:
            result = session.query(func.sum(models.InstanceBackup.size)).scalar()
        return result or 0
