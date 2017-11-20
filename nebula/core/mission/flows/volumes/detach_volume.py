# -*- coding: utf-8 -*-
import string
import arrow
from taskflow.patterns import linear_flow
from nebula.core import constants

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    nova import get_client as get_nova_client
from nebula.openstack.common import log
from nebula.core.i18n import _
from nebula.core.resource_monitor import monitor

LOG = log.getLogger(__name__)
ACTION = "volume:detach"


class DetachVolumeTask(task.NebulaTask):

    default_provides = 'volume'

    def __init__(self):
        super(DetachVolumeTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始卸载数据卷"))
        resource = managers.volumes.get(self.admin_context, resource_id)
        instance = managers.instances.get(self.admin_context, resource.instance_id)

        self.update_job_state_desc(job_id, _(u"申请卸载数据卷"))
        get_nova_client().volumes.delete_server_volume(
            instance.instance_uuid,
            resource.volume_uuid
        )
        self.update_job_state_desc(job_id, _(u"申请卸载数据卷资成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"卸载数据卷资源失败"))
        self.log_current_task_failures(*args, **kwargs)


class PersistentVolumeDetach(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentVolumeDetach, self).__init__(addons=[ACTION])

    def _wait_detach_volume(self, resource_id):
        """等待数据卷完成(通过消息改变状态后)."""

        def checker():
            volume = managers.volumes.get(self.admin_context, resource_id)
            LOG.info("The volume current state:%s" % volume.status)
            if volume.status == constants.VOLUME_AVAILABLE:
                return True
            elif volume.status == constants.VOLUME_ERROR:
                raise monitor.ResourceFailureError('Error Volume state')
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait()
    
    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新数据卷卸载信息到数据库，等待消息通知"))

        request_context = self.get_request_context(**kwargs)

        managers.volumes.update(
            request_context,
            resource_id,
            status=constants.VOLUME_DETACHING
        )
        
        self.update_job_state_desc(job_id, _(u"数据卷卸载中"))
        # 等待通知改变状态
        try:
            self._wait_detach_volume(resource_id)
        except Exception as ex:
            self.update_job_state_desc(job_id, _(u"数据卷卸载失败"))
            raise ex
        
        self.update_job_state_desc(job_id, _(u"存入数据卷卸载信息到数据库"))
        params = dict(
            instance_id=None,
            status=constants.VOLUME_AVAILABLE
        )
        managers.volumes.update(self.admin_context, resource_id, **params)

        self.update_job_state_desc(job_id, _(u"卸载数据卷成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        request_context = self.get_request_context(**kwargs)
        managers.volumes.update(
            request_context,
            kwargs["resource_id"],
            status=constants.VOLUME_IN_USE
        )
        self.update_job_state_desc(job_id, _(u"卸载数据卷失败"))


def get_detach_data_volume_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        DetachVolumeTask(),
        PersistentVolumeDetach()
    )
    return flow


class DataVolumeDetachBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(DataVolumeDetachBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_detach_data_volume_flow
        )

    def prepare_resource(self, *args, **kwargs):
        return managers.volumes.get(self.context, kwargs["resource_id"])

    def associate_resource_with_job(self, resource, job):
        managers.volumes.update(self.context, resource.id, job_id=job.id)
        # 同时更新虚拟机的任务状态
        managers.instances.update(self.context, resource.instance.id, dict(job_id=job.id))


class InstanceDataVolumeDetachBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(InstanceDataVolumeDetachBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_detach_data_volume_flow
        )

    def prepare_resource(self, *args, **kwargs):
        return managers.volumes.get(self.context, kwargs["volume_id"])

    def associate_resource_with_job(self, resource, job):
        managers.volumes.update(self.context, resource.id, job_id=job.id)
        managers.instances.update(self.context, resource.instance.id, dict(job_id=job.id))

