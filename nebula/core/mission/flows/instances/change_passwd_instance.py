# coding=utf-8
from taskflow.patterns import linear_flow

from nebula.core.common.openstack import vm_states
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.openstack_clients import nova
from nebula.core.resource_monitor import monitor as res_mon
from nebula.core.i18n import _

from .base import InstanceURDBuilder

ACTION = 'instance:change-password'


class ChangePasswordTask(task.NebulaTask):

    def execute(self, job_id, instance_uuid, password, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更新虚拟机密码"))
        nova.get_client().servers.change_admin_password(instance_uuid, password)

        def checker():
            instance_obj = managers.instances.get_by_uuid(
                self.admin_context, instance_uuid
            )

            if not instance_obj:
                # 严重错误, 没有找到相应实体
                raise res_mon.ResourceFailureError('Entity not found')
            elif instance_obj['vm_state'] == vm_states.ERROR:
                raise res_mon.ResourceFailureError('Error VM state')
            elif instance_obj['task_state'] is None:
                return True
            return False

        monitor = res_mon.ResourceChangeMonitor(checker)
        # 等待Resize完成或者错误(包括超时)
        monitor.wait()

        self.update_job_state_desc(job_id, _(u"修改虚拟机密码成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, _(u"修改虚拟机密码失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        ChangePasswordTask(),
    )
    return flow


class InstanceChangePasswordBuilder(InstanceURDBuilder):

    def __init__(self, context, resource_kwargs=None, store=None):
        super(InstanceChangePasswordBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            store=store)

    def prepare_resource(self, *args, **kwargs):
        instance=managers.instances.get(self.context, kwargs["resource_id"])
        self.store.update(dict(
            instance_uuid=instance.instance_uuid,
            password=kwargs["password"]
        ))
        return instance

    def associate_resource_with_job(self, resource, job):
        managers.instances.update(self.context,
                                  resource.id, dict(job_id=job.id))


