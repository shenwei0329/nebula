# coding=utf-8
from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.openstack_clients import nova
from nebula.core.i18n import _

from .base import InstanceURDBuilder

ACTION = 'instance:change-iops'


class ChangeIOPSTask(task.NebulaTask):

    def execute(self, job_id, instance_uuid, iops, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更新虚拟机IOPS"))
        nova.get_client().servers.change_iops(instance_uuid, iops)
        self.update_job_state_desc(job_id, _(u"更新虚拟机IOPS成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        if self.is_current_task_ok(kwargs['result']):
            instance_obj = managers.instances.get_by_uuid(
                self.admin_context, kwargs['instance_uuid']
            )
            # 尝试更新虚拟机iops为原来的值
            try:
                nova.get_client().servers.change_iops(
                    self.admin_context, instance_obj['iops']
                )
            except Exception as ex:
                self.get_logger().exception(ex)
        else:
            self.update_job_state_desc(job_id, _(u"更新虚拟机IOPS失败"))


class PersistentIOPSTask(task.NebulaTask):

    def execute(self, job_id, resource_id, iops, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始同步数据库"))
        values = dict(
            iops=iops
        )
        managers.instances.update(self.admin_context, resource_id,
                                  values)
        self.update_job_state_desc(job_id, _(u"更新虚拟机IOPS成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新虚拟机IOPS失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        ChangeIOPSTask(),
        PersistentIOPSTask(),
    )
    return flow


class InstanceChangeIOPSBuilder(InstanceURDBuilder):

    def __init__(self, context, resource_kwargs=None, store=None):
        super(InstanceChangeIOPSBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            store=store)

