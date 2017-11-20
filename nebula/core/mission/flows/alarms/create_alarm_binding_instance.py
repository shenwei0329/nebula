# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core import quota
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.openstack.common import log
from nebula.core.i18n import _
from nebula.core.openstack_clients.ceilometer import get_client
import string
import os
import simplejson

QUOTAS = quota.QUOTAS
LOG = log.getLogger(__name__)
ACTION = "alarm_binding_instance:create"


class CreateAlarmBindingInstanceTask(task.NebulaTask):

    default_provides = 'alarm_binding'

    def __init__(self):
        super(CreateAlarmBindingInstanceTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, share_alarm, rule_list, instance_id, type, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始绑定告警"))
        host_name = None
        if type == "host":
            host = managers.compute_nodes.get(None, instance_id)
            if host:
                host_name = host.os_hostname

        params = list()
        for rule in rule_list:

            url_common_str = "http://%s/systems/alert" % os.popen('hostname').read().strip('\n')

            url_alarm_actions = "%s/%s/%s/%s/%s" % \
                                (url_common_str, type, instance_id, rule['id'], "alarm")
            url_ok_actions = "%s/%s/%s/%s/%s" % \
                                (url_common_str, type, instance_id, rule['id'], "ok")
            url_insufficient_data_actions = "%s/%s/%s/%s/%s" % \
                                (url_common_str, type, instance_id, rule['id'], "no_data")

            param = dict(name=share_alarm['name']+'##'+instance_id+'::'+str(rule['id']),
                        description=share_alarm['description'],
                        type='threshold',
                        enable=share_alarm['enabled'],
                        repeat_actions=share_alarm['repeat_actions'],
                        threshold_rule=dict(
                                            comparison_operator=rule['comparison_operator'],
                                            evaluation_periods=rule['evaluation_periods'],
                                            exclude_outliers=rule['exclude_outlier'],
                                            meter_name=rule['meter_name'],
                                            period=rule['period'],
                                            query=[{
                                                    'field':"resource_id",
                                                    'op':'eq',
                                                    'type':"string",
                                                    'value':instance_id if not type == 'host' else host_name
                                                    }],
                                            statistic=rule['statistic'],
                                            threshold=rule['threshold']
                                            ),
                        alarm_actions=[url_alarm_actions],
                        ok_actions=[url_ok_actions],
                        insufficient_data_actions=[url_insufficient_data_actions],
                        time_constraints=[{
                                "description":"time constraint",
                                "duration":10800,
                                "name":"Meter Constraint",
                                "start":rule['start']
                                #"timezone":"UTC"
                            }]
                        )

            params.append(param)

        rt = get_client().alarms.create_batch(params)
        self.update_job_state_desc(job_id, _(u"绑定告警成功"))

        return rt

    def revert(self, job_id, resource_id, *args, **kwargs):

        self.update_job_state_desc(job_id, _(u"绑定告警失败"))


class CreateAlarmBindingInstanceEntryTask(task.NebulaTask):

    def execute(self, job_id, resource_id, share_alarm, rule_list, alarm_binding, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始保存告警绑定到数据库"))

        if alarm_binding:
            for alarm in alarm_binding:
                idx = alarm['name'].find('::')
                rule_id = string.atoi(alarm['name'][idx+2:], 10)
                alarm_cml_id = alarm['alarm_id']
                instance_id = alarm['threshold_rule']['query'][0]['value']

                rt = managers.alarm_rules.get(self.admin_context, rule_id)
                alarm_id = rt.alarm.id

                '''
                #@since 识别主机添加的代码
                '''
                host = None
                try:
                    host = managers.compute_nodes.get_by_hostname(self.admin_context, instance_id)
                except Exception as e:
                    #这里主
                    pass
                '''
                End
                '''

                managers.alarm_bindings.create(creator=user_id,
                                                alarm_tmpl_id=alarm_id,
                                                rule_id=rule_id,
                                                alarm_cml_id=alarm_cml_id,
                                                instance_id=instance_id if not host else host.id
        )

        self.update_job_state_desc(job_id, _(u"绑定告警成功"))

    def revert(self, job_id, resource_id, alarm_binding, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)

        for alarm in alarm_binding:
            managers.alarm_bindings.delete_by(alarm_cml_id=alarm['alarm_id'])

        self.update_job_state_desc(job_id, _(u"绑定告警失败"))


def get_create_alarm_binding_instance_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreateAlarmBindingInstanceTask(),
             CreateAlarmBindingInstanceEntryTask()
    )
    return flow


class AlarmBindingInstanceCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(AlarmBindingInstanceCreateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_create_alarm_binding_instance_flow
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        share_alarm = managers.alarms.get(self.context, kwargs['alarm_tmpl_id'])
        rule_list = managers.alarm_rules.get_by(self.context, alarm_id=kwargs['alarm_tmpl_id'])

        self.store['share_alarm'] = share_alarm
        self.store['rule_list'] = rule_list
        self.store['user_id'] = self.context.user_id

        rt = None
        if kwargs['type'] == 'vm':
            rt = managers.instances.get_by(None, instance_uuid=kwargs['instance_id'])
        elif kwargs['type'] == 'host':
            rt = managers.compute_nodes.get(None, kwargs['instance_id'])

        return rt

    def associate_resource_with_job(self, resource, job):
        if self.store['type'] == 'vm':
            managers.instances.update(self.context, resource.id, dict(job_id=job.id))
        elif self.store['type'] == 'host':
            managers.compute_nodes.update(self.context, resource.id, dict(job_id=job.id))
