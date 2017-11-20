# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core import quota
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.openstack.common import log
from nebula.core.i18n import _
from nebula.core.openstack_clients.ceilometer import get_client

QUOTAS = quota.QUOTAS
LOG = log.getLogger(__name__)
ACTION = "alarm_binding_instance:delete"


class DeleteAlarmBindingInstanceTask(task.NebulaTask):

    default_provides = 'alarm_binding'

    def __init__(self):
        super(DeleteAlarmBindingInstanceTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, binding_list, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始解绑告警"))

        rt_list = list()
        for item in binding_list:
            rt = get_client().alarms.delete(item['alarm_cml_id'])
            rt_list.append(rt)

        self.update_job_state_desc(job_id, _(u"解绑告警成功"))

        return binding_list

    def revert(self, job_id, resource_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"解绑告警失败"))


class DeleteAlarmBindingInstanceEntryTask(task.NebulaTask):

    def execute(self, job_id, resource_id, binding_list, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始从数据库解绑告警"))

        for item in binding_list:
            managers.alarm_bindings.delete_by(alarm_cml_id=item['alarm_cml_id'])

        self.update_job_state_desc(job_id, _(u"解绑告警成功"))

    def revert(self, job_id, resource_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"解绑告警失败"))


def get_delete_alarm_binding_instance_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeleteAlarmBindingInstanceTask(),
             DeleteAlarmBindingInstanceEntryTask()
    )
    return flow


class AlarmBindingInstanceDeleteBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(AlarmBindingInstanceDeleteBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_delete_alarm_binding_instance_flow
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)

        binding_list = managers.alarm_bindings.get_by(self.context, instance_id=kwargs['resource'])
        if not binding_list:
            raise Exception

        self.store['binding_list'] = binding_list

        rt = None
        if kwargs['type'] == 'vm':
            rt = managers.instances.get_by(None, instance_uuid=kwargs['resource'])
        elif kwargs['type'] == 'host':
            rt = managers.compute_nodes.get(None, kwargs['resource'])

        return rt


    def associate_resource_with_job(self, resource, job):
        if self.store['type'] == 'vm':
            managers.instances.update(self.context, resource.id, dict(job_id=job.id))
        elif self.store['type'] == 'host':
            managers.compute_nodes.update(self.context, resource.id, dict(job_id=job.id))
