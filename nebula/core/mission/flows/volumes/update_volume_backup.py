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
ACTION = "volume_backup:update"


class UpdateVolumeBackupTask(task.NebulaTask):

    default_provides = 'volume_backup'

    def __init__(self):
        super(UpdateVolumeBackupTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, name, volume_backup_uuid, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始修改数据卷备份"))
        self.update_job_state_desc(job_id, _(u"申请修改数据卷备份"))

        get_cinder_client().volume_snapshots.update(
            volume_backup_uuid,
            display_name=name
        )
        self.update_job_state_desc(job_id, _(u"申请修改数据卷资源备份成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新数据卷资源备份失败"))
        self.log_current_task_failures(*args, **kwargs)


class PersistentVolumeBackupUpdate(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentVolumeBackupUpdate, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, name, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入数据卷备份更新申请到数据库"))
        managers.volume_backups.update(self.admin_context, resource_id, name=name)

        self.update_job_state_desc(job_id, _(u"存入数据卷备份更新申请到数据库成功"))
        self.update_job_state_desc(job_id, _(u"更新数据卷备份成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"更新数据卷备份失败"))


def get_update_volume_backup_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        UpdateVolumeBackupTask(),
        PersistentVolumeBackupUpdate()
    )
    return flow


class VolumeBackupUpdateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(VolumeBackupUpdateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_update_volume_backup_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        vb = managers.volume_backups.get(self.context, kwargs["resource_id"])
        self.store.update(kwargs)
        self.store["volume_backup_uuid"] = vb.volume_backup_uuid
        return vb

    def associate_resource_with_job(self, resource, job):
        managers.volume_backups.update(self.context, resource.id, job_id=job.id)
