# -*- coding: utf-8 -*-
import re
from taskflow.patterns import linear_flow
from nebula.core import constants

from nebula.core import quota
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    cinder import get_client as get_cinder_client
from nebula.openstack.common import log
from nebula.core.i18n import _
from nebula.core.resource_monitor import monitor

QUOTAS = quota.QUOTAS
LOG = log.getLogger(__name__)
ACTION = "volume:delete"


class DeleteVolumeTask(task.NebulaTask):

    default_provides = 'volume'

    def __init__(self):
        super(DeleteVolumeTask, self).__init__(addons=[ACTION])

    def _wait_delete_volume(self, resource_id):
        """等待数据卷删除完成，然后真正删除数据卷(通过消息改变状态后)."""

        def checker():
            volume = managers.volumes.get_by(self.admin_context, id=resource_id)
            if not volume or volume.status == constants.VOLUME_DELETED:
                return True
            elif volume.status == constants.VOLUME_ERROR:
                raise res_mon.ResourceFailureError('Error Volume Backup state')
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait()

    def execute(self, job_id, resource_id, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除数据卷"))
        resource = managers.volumes.get(self.admin_context, resource_id)

        if resource.volume_backups:
            raise Exception(u"Backup volume exist and can not be deleted")

        self.update_job_state_desc(job_id, _(u"正在删除数据卷"))
        if resource != constants.VOLUME_DELETED:
            is_wait = True
            try:
                get_cinder_client().volumes.delete(
                    resource.volume_uuid
                )
            except Exception as err:
                error = str(err)
                if re.search(r'The resource could not be found', error):
                    self.update_job_state_desc(job_id, _(u"数据卷已经不存在！"))
                    is_wait = False
                    pass
                else:
                    raise err
            # 等待通知改变状态
            if is_wait:
                self._wait_delete_volume(resource_id)
        self.update_job_state_desc(job_id, _(u"申请删除数据卷成功"))

    def revert(self, job_id,  user_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"删除数据卷失败"))
        self.log_current_task_failures(*args, **kwargs)


class PersistentVolumeDelete(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentVolumeDelete, self).__init__(addons=[ACTION])

    def execute(self, job_id, user_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除数据卷的数据库记录"))
        request_context = self.get_request_context(**kwargs)

        volume = managers.volumes.get(request_context, resource_id)
        reservations = QUOTAS.reserve(request_context,
                                      user_id=volume.owner_id,
                                      **{'volumes': -volume.size})
        try:
            managers.volumes.delete_by(
                id=resource_id
            )
        except Exception as err:
            QUOTAS.rollback(request_context, reservations, user_id=user_id)
            self.update_job_state_desc(job_id, _(u"删除存数据卷的数据库记录失败：%s" % str(err)))
            raise err
        # commit volume quota
        QUOTAS.commit(request_context, reservations, user_id=user_id)

        self.update_job_state_desc(job_id, _(u"删除存数据卷的数据库记录成功"))
        self.update_job_state_desc(job_id, _(u"删除数据卷成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"删除数据卷的数据库记录失败"))


def get_delete_volume_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        DeleteVolumeTask(),
        PersistentVolumeDelete()
    )
    return flow


class VolumeDeleteBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(VolumeDeleteBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_delete_volume_flow
        )

    def prepare_resource(self, *args, **kwargs):
        volume = managers.volumes.get(self.context, kwargs["resource_id"])
        self.store.update(
            user_id=volume.owner_id,
        )
        return volume

    def associate_resource_with_job(self, resource, job):
        managers.volumes.update(self.context, resource.id, job_id=job.id)
