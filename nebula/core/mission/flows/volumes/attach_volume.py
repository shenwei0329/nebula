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
ACTION = "volume:attach"


class AttachVolumeTask(task.NebulaTask):

    default_provides = 'volume_attach'

    def __init__(self):
        super(AttachVolumeTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, instance_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始挂载数据卷"))
        resource = managers.volumes.get(self.admin_context, resource_id)
        instance = managers.instances.get(self.admin_context, instance_id)

        volume = get_nova_client().volumes.create_server_volume(
            instance.instance_uuid,
            resource.volume_uuid,
            None
        )

        self.update_job_state_desc(job_id, _(u"申请数据卷挂载"))
        self.update_job_state_desc(job_id, _(u"申请数据卷挂载成功"))
        return volume._info

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        params = dict(
            instance_id=None
        )
        managers.volumes.update(self.admin_context, kwargs["resource_id"], **params)
        self.update_job_state_desc(job_id, _(u"挂载数据卷失败"))


class PersistentVolumeAttach(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentVolumeAttach, self).__init__(addons=[ACTION])

    def _wait_attach_volume(self, resource_id):
        """等待数据卷完成(通过消息改变状态后)."""

        def checker():
            volume = managers.volumes.get(self.admin_context, resource_id)
            LOG.info("The volume current state:%s" % volume.status)
            if volume.status == constants.VOLUME_IN_USE:
                return True
            elif volume.status == constants.VOLUME_ERROR:
                raise monitor.ResourceFailureError('Error Volume state')
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait()

    def execute(self, job_id, resource_id, instance_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新数据卷挂载信息到数据库，等待消息通知"))

        request_context = self.get_request_context(**kwargs)

        managers.volumes.update(
            request_context,
            resource_id,
            status=constants.VOLUME_ATTACHING
        )
        
        self.update_job_state_desc(job_id, _(u"数据卷挂载中"))
        # 等待通知改变状态
        try:
            self._wait_attach_volume(resource_id)
        except Exception as ex:
            self.update_job_state_desc(job_id, _(u"数据卷挂载失败"))
            raise ex
        
        self.update_job_state_desc(job_id, _(u"数据卷挂载保存到数据库"))
        params = dict(
            status=constants.VOLUME_IN_USE,
            attach_time=arrow.utcnow().to('+08:00').format('YYYY-MM-DD HH:mm:ss')
        )
        managers.volumes.update(self.admin_context, resource_id, **params)

        self.update_job_state_desc(job_id, _(u"数据卷挂载保存到数据库成功"))
        self.update_job_state_desc(job_id, _(u"挂载数据卷成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        request_context = self.get_request_context(**kwargs)
        managers.volumes.update(
            request_context,
            kwargs["resource_id"],
            status=constants.VOLUME_AVAILABLE
        )
        self.update_job_state_desc(job_id, _(u"挂载数据卷失败"))


def get_attach_data_volume_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(AttachVolumeTask(),
             PersistentVolumeAttach())
    return flow


class DataVolumeAttachBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(DataVolumeAttachBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_attach_data_volume_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(dict(
            instance_id=kwargs["instance_id"]
        ))
        params = dict(
            instance_id=kwargs["instance_id"]
        )
        return managers.volumes.update(self.context, kwargs["volume_id"], **params)

    def associate_resource_with_job(self, resource, job):
        managers.volumes.update(self.context, resource.id, job_id=job.id)
        # 同时更新虚拟机的任务状态
        managers.instances.update(self.context,
                                  self.store["instance_id"],
                                  dict(job_id=job.id))

