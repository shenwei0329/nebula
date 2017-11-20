# -*- coding: utf-8 -*-
import re
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
ACTION = "volume_backup:delete"


class DeleteVolumeBackupTask(task.NebulaTask):

    default_provides = 'volume'

    def __init__(self):
        super(DeleteVolumeBackupTask, self).__init__(addons=[ACTION])

    def _wait_delete_volume_backup(self, resource_id):
        """等待数据卷备份删除完成，真正删除备份卷(通过消息改变状态后)."""

        def checker():
            vb = managers.volume_backups.get(self.admin_context, resource_id)
            if not vb or vb.status == constants.VOLUME_DELETED:
                return True
            elif vb.status == constants.VOLUME_ERROR:
                raise res_mon.ResourceFailureError('Error Volume Backup state')
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait()

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除数据卷备份"))
        resource = managers.volume_backups.get(self.admin_context, resource_id)

        self.update_job_state_desc(job_id, _(u"正在删除数据卷备份"))
        if resource != constants.VOLUME_DELETED:
            is_wait = True
            try:
                get_cinder_client().volume_snapshots.delete(
                    resource.volume_backup_uuid
                )
            except Exception as err:
                error = str(err)
                if re.search(r'The resource could not be found', error):
                    self.update_job_state_desc(job_id, _(u"备份已经不存在！"))
                    is_wait = False
                    pass
                else:
                    raise err
            # 等待通知改变状态
            if is_wait:
                self._wait_delete_volume_backup(resource_id)
        self.update_job_state_desc(job_id, _(u"申请删除数据卷备份成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"申请数据卷备份删除失败"))


class PersistentVolumeBackup(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentVolumeBackup, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除数据卷备份的数据库记录"))
        managers.volume_backups.delete_by(
            id=resource_id
        )
        self.update_job_state_desc(job_id, _(u"删除存数据卷备份的数据库记录成功"))
        self.update_job_state_desc(job_id, _(u"删除数据卷备份成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"删除数据卷备份数据库记录失败"))


def get_delete_volume_backup_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        DeleteVolumeBackupTask(),
        PersistentVolumeBackup()
    )
    return flow


class VolumeBackupDeleteBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(VolumeBackupDeleteBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_delete_volume_backup_flow
        )

    def prepare_resource(self, *args, **kwargs):
        params = dict(
            status=constants.VOLUME_DELETING
        )
        return managers.volume_backups.update(self.context, kwargs["resource_id"], **params)

    def associate_resource_with_job(self, resource, job):
        managers.volume_backups.update(self.context, resource.id, job_id=job.id)
