# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = "alarm:modify"


class ModifyAlarmTask(task.NebulaTask):

    default_provides = 'alarm'

    def __init__(self):
        super(ModifyAlarmTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始修改告警"))
        self.update_job_state_desc(job_id, _(u"修改告警成功"))


    def revert(self, job_id, resource_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"修改告警失败"))


class ModifyAlarmEntryTask(task.NebulaTask):

    def execute(self, job_id, resource_id, alarm_name, alarm_description, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始保存告警到数据库"))

        LOG.info(alarm_description)
        managers.alarms.update(self.admin_context, resource_id, dict(name=alarm_name, description=alarm_description))

        self.update_job_state_desc(job_id, _(u"修改告警成功"))

    def revert(self, job_id, resource_id, name, description, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"修改告警失败"))


def get_modify_alarm_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(ModifyAlarmTask(),
             ModifyAlarmEntryTask()
    )
    return flow


class AlarmModifyBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(AlarmModifyBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_modify_alarm_flow
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        rt = managers.alarms.get(self.context, kwargs['alarm_id'])
        self.store.update(rt)

        return rt

    def associate_resource_with_job(self, resource, job):
        managers.alarms.update(self.context, resource.id, dict(job_id=job.id))
