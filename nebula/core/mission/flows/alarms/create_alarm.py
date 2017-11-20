# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core import quota
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.openstack.common import log
from nebula.core.i18n import _
import json

QUOTAS = quota.QUOTAS
LOG = log.getLogger(__name__)
ACTION = "alarm:create"


class CreateAlarmTask(task.NebulaTask):

    default_provides = 'alarm'

    def __init__(self):
        super(CreateAlarmTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建告警"))
        self.update_job_state_desc(job_id, _(u"创建告警成功"))


    def revert(self, job_id, resource_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"创建告警失败"))


class CreateAlarmEntryTask(task.NebulaTask):

    def execute(self, job_id, resource_id, meter_rules, alarm_action, ok_action, insufficient_data_action,
                alarm_period, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始保存告警到数据库"))

        LOG.info(meter_rules)
        if meter_rules is not None:
            decodejson = json.loads(meter_rules, encoding='UTF-8')

            for item in decodejson:
                managers.alarm_rules.create(creator=user_id,
                                            meter_name=item['meter_type'],
                                            alarm_id=resource_id,
                                            comparison_operator=item['comparison_operator'],
                                            threshold=item['threshold'],
                                            alarm_actions=alarm_action,
                                            ok_actions=ok_action,
                                            insufficient_data_actions=insufficient_data_action,
                                            start="*/%s * * * *" % alarm_period
                )

        self.update_job_state_desc(job_id, _(u"创建告警成功"))

    def revert(self, job_id, resource_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)

        managers.alarms.delete(resource_id)
        items = managers.alarm_rules.get_by(self.admin_context, alarm_id=resource_id)
        for item in items:
            managers.alarm_rules.delete(item.id)

        self.update_job_state_desc(job_id, _(u"创建告警失败"))


def get_create_alarm_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreateAlarmTask(),
             CreateAlarmEntryTask()
    )
    return flow


class AlarmCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(AlarmCreateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_create_alarm_flow
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        self.store['user_id'] = self.context.user_id

        rt = managers.alarms.create(creator=self.context.user_id,
                                    name=kwargs['alarm_name'],
                                    description='',
                                    type=kwargs['alarm_type'],
                                    enabled=True,
                                    repeat_actions=False,
                                    state=None,
                                    state_timestamp=None,
                                    timestamp=None,
                                    threshold_rule=None
        )

        return rt

    def associate_resource_with_job(self, resource, job):
        managers.alarms.update(self.context, resource.id, dict(job_id=job.id))
