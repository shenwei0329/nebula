# -*- coding: utf-8 -*-
import re
from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    neutron import get_client as get_neutron_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = "security_group_rule:delete"


class DeleteSecurityGroupRuleTask(task.NebulaTask):

    default_provides = 'security_group_rule'

    def __init__(self):
        super(DeleteSecurityGroupRuleTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除规则"))
        resource = managers.security_group_rules.get(self.admin_context, resource_id)
        try:
            get_neutron_client().delete_security_group_rule(resource.security_group_rule_uuid)
        except Exception as err:
            error = str(err)
            self.update_job_state_desc(job_id, _(error))
            if re.search(r'[\w|-]{36}|None\sdoes not exist', error):
                self.update_job_state_desc(job_id, _(u"规则资源已经被删除，可以忽略！"))
                pass
            else:
                raise err
        self.update_job_state_desc(job_id, _(u"删除规则资源成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"删除规则资源失败"))


class DeleteSecurityGroupRuleEntryTask(task.NebulaTask):
    def execute(self, job_id, resource_id, **kwargs):
        # 删除数据库中私有网络
        self.update_job_state_desc(job_id, _(u"开始删除数据库规则"))
        managers.security_group_rules.delete_by(id=resource_id)
        self.update_job_state_desc(job_id, _(u"删除规则成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"删除规则失败"))


def get_delete_security_group_rule_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeleteSecurityGroupRuleTask(), DeleteSecurityGroupRuleEntryTask())
    return flow


class SecurityGroupRuleDeleteBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(SecurityGroupRuleDeleteBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_delete_security_group_rule_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        return managers.security_group_rules.get(self.context,
                                                 kwargs['resource_id'])

    def associate_resource_with_job(self, resource, job):
        managers.security_group_rules.update(self.context,
                                             resource.id, dict(job_id=job.id))

