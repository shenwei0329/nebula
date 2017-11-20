# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow
from nebula.core import constants

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    cinder import get_client as get_cinder_client
from nebula.openstack.common import log
from nebula.core.i18n import _
from nebula.core.resource_monitor import monitor

LOG = log.getLogger(__name__)
ACTION = "volume_backup:create"


class CreateVolumeBackupTask(task.NebulaTask):

    default_provides = 'volume_backup'

    def __init__(self):
        super(CreateVolumeBackupTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, name, volume_uuid, volume_backup_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建数据卷备份"))
        self.update_job_state_desc(job_id, _(u"申请创建数据卷备份"))

        volume_backup = get_cinder_client().volume_snapshots.\
            create(volume_uuid, display_name=name)

        self.update_job_state_desc(job_id, _(u"申请数据卷资源备份成功"))

        return volume_backup._info

    def revert(self, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        managers.volume_backups.delete_by(id=kwargs["volume_backup_id"])
        volume_backup = kwargs['result']
        if self.is_current_task_ok(volume_backup):
            get_cinder_client().volume_snapshots.delete(volume_backup['id'])


class PersistentVolumeBackup(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentVolumeBackup, self).__init__(addons=[ACTION])

    def _wait_volume_backup_create(self, resource_id):
        """等待数据卷备份完成(通过消息改变状态后)."""

        def checker():
            volume = managers.volume_backups.get(self.admin_context, resource_id)

            if volume.status == constants.VOLUME_AVAILABLE:
                return True
            elif volume.status == constants.VOLUME_ERROR:
                raise res_mon.ResourceFailureError('Error Volume Backup state')
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait()

    def execute(self, job_id, resource_id, volume_backup, user_id, volume_backup_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入数据卷备份到数据库"))

        vb = managers.volume_backups.update(
            self.admin_context,
            volume_backup_id,
            volume_backup_uuid=volume_backup["id"]
        )

        self.update_job_state_desc(job_id, _(u"数据卷备份中"))
        # 等待通知改变状态
        self._wait_volume_backup_create(vb.id)

        self.update_job_state_desc(job_id, _(u"存入数据卷备份到数据库成功"))
        self.update_job_state_desc(job_id, _(u"创建数据卷备份成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"创建数据卷备份失败"))


def get_create_volume_backup_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        CreateVolumeBackupTask(),
        PersistentVolumeBackup()
    )
    return flow


class VolumeBackupCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(VolumeBackupCreateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_create_volume_backup_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        volume_id = kwargs["resource_id"]
        volume = managers.volumes.get(self.context, volume_id)
        vb = managers.volume_backups.create(
            volume.owner_id,
            volume_id=volume_id,
            name=kwargs["name"]
        )
        params = dict(
            volume_uuid=volume.volume_uuid,
            name=kwargs["name"],
            user_id=volume.owner_id,
            volume_backup_id=vb.id
        )

        self.store.update(params)
        return volume

    def associate_resource_with_job(self, resource, job):
        managers.volumes.update(self.context, resource.id, job_id=job.id)
