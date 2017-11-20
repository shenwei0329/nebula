# -*- coding: utf-8 -*-
import logging

from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.openstack_clients import nova
from nebula.core.i18n import _

from .base import InstanceURDBuilder

LOG = logging.getLogger(__name__)

ACTION = 'instance:modify'


class ModifyOSInstanceTask(task.NebulaTask):
    def __init__(self):
        super(ModifyOSInstanceTask, self).__init__()

    def execute(self, job_id, resource_id, instance_uuid, display_name,
                **kwargs):
        self.update_job_state_desc(job_id, _(u"正在更新虚拟机"))
        LOG.error("\n %s" % display_name)
        nova.get_client().servers.update(instance_uuid, display_name)

    def revert(self, job_id, instance_uuid, display_name, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        result = kwargs['result']
        if self.is_current_task_ok(result):
            nova.get_client().servers.update(instance_uuid, display_name)
        else:
            self.update_job_state_desc(job_id, _(u"更新虚拟机失败"))


class ModifyInstanceEntityTask(task.NebulaTask):
    def execute(self, job_id, resource_id, display_name, display_description, **kwargs):
        # 更新数据库中虚拟机条目
        managers.instances.update_by_id(
            self.admin_context,
            resource_id,
            {
                'display_name': display_name,
                'display_description': display_description,
            })
        self.update_job_state_desc(job_id, _(u"更新虚拟机成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"更新虚拟机失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        ModifyOSInstanceTask(),
        ModifyInstanceEntityTask()
    )
    return flow


class InstanceModifyBuilder(InstanceURDBuilder):
    def __init__(self, context, resource_kwargs=None, store=None):
        super(InstanceModifyBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            store=store)
