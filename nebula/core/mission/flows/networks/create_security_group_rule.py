# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    neutron import get_client as get_neutron_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = "security_group_rule:create"


class CreateSecurityGroupRuleTask(task.NebulaTask):

    default_provides = 'security_group_rule'

    def __init__(self):
        super(CreateSecurityGroupRuleTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, protocol, port_range_min,
                port_range_max, remote_ip_prefix, remote_ip_suffix,
                security_group_uuid, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建规则"))
        if remote_ip_prefix and remote_ip_suffix:
            remote_ip_prefix = "/".join([str(remote_ip_prefix), str(remote_ip_suffix)])
        else:
            remote_ip_prefix = None
        params = dict(
            security_group_id=security_group_uuid,
            ethertype="IPv4",
            direction="ingress",
            remote_ip_prefix=remote_ip_prefix
        )

        if protocol in ('tcp', 'TCP', 'udp', 'UDP'):
            params.update(dict(
                protocol=protocol,
                port_range_min=port_range_min,
                port_range_max=port_range_max
            ))
        elif protocol in ('ip', 'IP'):
            params["protocol"] = None
        else:
            params["protocol"] = protocol

        LOG.info("create security group rule params:%s" % params)

        sgr = get_neutron_client().create_security_group_rule(
            body={'security_group_rule': params}
        )
        self.update_job_state_desc(job_id, _(u"创建规则成功"))

        return sgr['security_group_rule']

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        security_group_rule = kwargs['result']
        if self.is_current_task_ok(security_group_rule):
            get_neutron_client().delete_security_group_rule(security_group_rule['id'])
        self.update_job_state_desc(job_id, _(u"创建规则失败"))


class PersistentSecurityGroupRule(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentSecurityGroupRule, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, security_group_rule, name,
                protocol, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"规则存入数据库"))
        LOG.info("openstack return data: %s" % security_group_rule)

        managers.security_group_rules.create(
            user_id,
            security_group_id=resource_id,
            security_group_rule_uuid=security_group_rule.get("id"),
            name=name,
            direction=security_group_rule.get("direction", None),
            protocol=protocol,
            port_range_min=security_group_rule.get("port_range_min", None),
            port_range_max=security_group_rule.get("port_range_max", None),
            remote_ip_prefix=security_group_rule.get("remote_ip_prefix", None)
        )

        self.update_job_state_desc(job_id, _(u"规则存入数据库成功"))
        self.update_job_state_desc(job_id, _(u"创建规则成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"创建规则失败"))


def get_create_security_group_rule_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreateSecurityGroupRuleTask(),
             PersistentSecurityGroupRule())
    return flow


class SecurityGroupRuleCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(SecurityGroupRuleCreateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_create_security_group_rule_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        sg = managers.security_groups.get(self.context, kwargs["security_group_id"])
        self.store.update(kwargs)
        self.store.update(dict(
            security_group_uuid=sg.security_group_uuid,
            user_id=sg.owner_id
        ))
        return sg

    def associate_resource_with_job(self, resource, job):
        managers.security_groups.update(self.context, resource.id, job_id=job.id)
