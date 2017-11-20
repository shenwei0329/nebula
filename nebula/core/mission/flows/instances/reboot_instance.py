# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core.common.openstack import vm_states
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.openstack_clients import nova
from nebula.core.resource_monitor import monitor as res_mon
from nebula.core.i18n import _

from .base import InstanceURDBuilder

ACTION = 'instance:reboot'


class RebootOSInstanceTask(task.NebulaTask):
    def __init__(self):
        super(RebootOSInstanceTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, instance_uuid, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始重启虚拟机"))
        nova.get_client().servers.reboot(instance_uuid)

        def checker():
            instance_ref = managers.instances.get_by(
                self.admin_context, instance_uuid=instance_uuid)
            if not instance_ref:
                # 严重错误, 没有找到相应实体
                raise res_mon.ResourceFailureError('Entity not found')
            elif instance_ref['vm_state'] == vm_states.ERROR:
                raise res_mon.ResourceFailureError('Error VM state')
            elif instance_ref['vm_state'] == vm_states.ACTIVE:
                # 状态为 active, 重启完成
                return True
            return False

        monitor = res_mon.ResourceChangeMonitor(checker)
        # 等待完成或错误(包括超时)
        monitor.wait()
        self.update_job_state_desc(job_id, _(u"重启虚拟机成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"重启虚拟机失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(RebootOSInstanceTask())
    return flow


class InstanceRebootBuilder(InstanceURDBuilder):
    def __init__(self, context, resource_kwargs=None, store=None):
        super(InstanceRebootBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            store=store)

    def associate_resource_with_job(self, resource, job):
        # 更新虚拟机状态为"active_"
        # 防止在checker开始时, 虚拟机数据库状态还未被及时更新, checker却认为虚拟机已恢复"active"状态
        managers.instances.update(self.context, resource.id, dict(
            job_id=job.id, vm_state=vm_states.ACTIVE_))
