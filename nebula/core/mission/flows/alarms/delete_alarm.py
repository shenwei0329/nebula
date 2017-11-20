# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core import quota
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.openstack.common import log
from nebula.core.i18n import _

QUOTAS = quota.QUOTAS
LOG = log.getLogger(__name__)
ACTION = "alarm:delete"


class DeleteAlarmTask(task.NebulaTask):

    default_provides = 'alarm'

    def __init__(self):
        super(DeleteAlarmTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除告警"))
        self.update_job_state_desc(job_id, _(u"删除告警成功"))

    def revert(self, job_id, resource_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"删除告警失败"))


class DeleteAlarmEntryTask(task.NebulaTask):

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始从数据库删除告警"))

        items = managers.alarm_rules.get_by(self.admin_context, alarm_id=resource_id)
        for item in items:
            managers.alarm_rules.delete(item.id)

        managers.alarms.delete(resource_id)

        self.update_job_state_desc(job_id, _(u"删除告警成功"))

    def revert(self, job_id, resource_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"删除告警失败"))


def get_delete_alarm_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeleteAlarmTask(),
             DeleteAlarmEntryTask()
    )
    return flow


class AlarmDeleteBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(AlarmDeleteBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_delete_alarm_flow
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        rt = managers.alarms.get(self.context, kwargs['alarm_id'])

        return rt

    def associate_resource_with_job(self, resource, job):
        managers.alarms.update(self.context, resource.id, dict(job_id=job.id))
