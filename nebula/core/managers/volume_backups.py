# -*- coding: utf-8 -*-
import time
from sqlalchemy.sql import func

from nebula.core import constants
from nebula.core.managers.base import BaseManager
from nebula.core.models import VolumeBackup


class VolumeBackupManager(BaseManager):

    def _get(self, context, volume_backup_id, session=None):
        return self.model_query(context,
                                VolumeBackup, session=session, user_only=False)\
            .filter_by(id=volume_backup_id).first()

    def get_by(self, context, session=None, **kwargs):
        return self.model_query(context,
                                VolumeBackup, session=session)\
            .filter_by(**kwargs).first()

    def get(self, context, volume_backup_id):
        return self._get(context, volume_backup_id)

    def create(self, user_id, **kwargs):
        with self.transactional() as session:
            volume_backup = VolumeBackup(
                volume_id=kwargs["volume_id"],
                volume_backup_uuid=kwargs.get("volume_backup_uuid", None),
                name=kwargs["name"],
                status=constants.VOLUME_BACKUPING,
                creator_id=user_id,
                owner_id=user_id)
            volume_backup.save(session)
        return volume_backup

    def update(self, context, volume_backup_id, **values):
        with self.transactional() as session:
            volume_backup = self._get(context, volume_backup_id, session)
            volume_backup.update(values)
        return volume_backup

    def update_by_uuid(self, context, volume_backup_uuid, **values):
        retry = 5
        with self.transactional() as session:
            volume_backup = self.get_by(context, session,
                                        volume_backup_uuid=volume_backup_uuid)
            i = 0
            while not volume_backup:
                if i >= retry:
                    break
                i += 1
                time.sleep(2)
                volume_backup = self.get_by(context, session,
                                            volume_backup_uuid=volume_backup_uuid)
            volume_backup.update(values)
            volume_backup.save(session)
        return volume_backup

    def delete_by(self, **kwargs):
        with self.transactional() as session:
            session.query(VolumeBackup).filter_by(**kwargs).delete()

    def list(self):
        with self.transactional() as session:
            return session.query(VolumeBackup).filter_by()

    def get_count_by_volume(self, volume_id):
        """
        :param volume_id:
        :return:
        """
        with self.transactional() as session:
            result = session.query(func.count(VolumeBackup.id)).filter(
                VolumeBackup.volume_id == volume_id
            ).scalar()
        return result or 0

