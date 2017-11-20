# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core import quota
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    neutron import get_client as get_neutron_client
from nebula.openstack.common import log
from nebula.core.i18n import _

QUOTAS = quota.QUOTAS
LOG = log.getLogger(__name__)
ACTION = "security_group:create"


class CreateSecurityGroupTask(task.NebulaTask):

    default_provides = 'security_group'

    def __init__(self):
        super(CreateSecurityGroupTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建虚拟防火墙"))
        resource = managers.security_groups.get(self.admin_context, resource_id)

        self.update_job_state_desc(job_id, _(u"申请虚拟防火墙资源"))
        sg = get_neutron_client().create_security_group(
            body={
                'security_group': {
                    'name': resource.name,
                    'description': resource.description}})
        self.update_job_state_desc(job_id, _(u"申请虚拟防火墙资源成功"))

        return sg['security_group']

    def revert(self, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        security_group = kwargs['result']
        if self.is_current_task_ok(security_group):
            get_neutron_client().delete_security_group(security_group['id'])


class PersistentSecurityGroup(task.NebulaTask):

    default_provides = 'persistent'

    def __init__(self):
        super(PersistentSecurityGroup, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, security_group, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入虚拟防火墙到数据库"))
        managers.security_groups.update(self.admin_context, resource_id, **{
            'security_group_uuid': security_group['id']
        })

        self.update_job_state_desc(job_id, _(u"存入虚拟防火墙到数据库成功"))
        self.update_job_state_desc(job_id, _(u"创建虚拟防火墙成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"创建虚拟防火墙失败"))


def get_create_security_group_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreateSecurityGroupTask(), PersistentSecurityGroup())
    return flow


class SecurityGroupCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(SecurityGroupCreateBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_create_security_group_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        reservations = QUOTAS.reserve(self.context,
                                      **{'firewalls': 1}
        )
        try:
            sg = managers.security_groups.create(self.context.user_id, **kwargs)
        except Exception as err:
            LOG.info("Create security group: %s." % err)
            QUOTAS.rollback(self.context, reservations)
            raise err
        else:
            QUOTAS.commit(self.context, reservations)

        return sg

    def associate_resource_with_job(self, resource, job):
        managers.security_groups.update(self.context, resource.id, job_id=job.id)


class UpdatePortSecurityGroupTask(task.NebulaTask):

    default_provides = 'r_port'

    def __init__(self):
        super(UpdatePortSecurityGroupTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, port_id, resource_id, security_group, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更新网卡防火墙"))

        # get all the security groups of one port
        values = dict(id = port_id)
        port_list = managers.ports.joined_by_sgroup_port(**values)

        sg_list = []
        for item in port_list:
            sg_list.append(item.security_group_uuid)
        # add the new security group
        sg_list.append(security_group['id'])

        port = managers.ports.get(self.admin_context, port_id)
        self.update_job_state_desc(job_id, _(u"申请更新网卡防火墙"))

        get_neutron_client().update_port(
            port.port_uuid,
            body={'port': {'security_groups': sg_list}}
        )
        self.update_job_state_desc(job_id, _(u"更新网卡防火墙成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新网卡防火墙失败"))


class PersistentPortSecurityGroup(task.NebulaTask):

    default_provides = 'persistent'

    def __init__(self):
        super(PersistentPortSecurityGroup, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, security_group, port_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入虚拟防火墙到数据库"))
        managers.security_groups.update(self.admin_context, resource_id, **{
            'security_group_uuid': security_group['id']
        })
        values = dict(security_group_id=resource_id)
        managers.ports.update(self.admin_context, port_id, **values)

        self.update_job_state_desc(job_id, _(u"存入虚拟防火墙到数据库成功"))
        self.update_job_state_desc(job_id, _(u"创建虚拟防火墙成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"创建虚拟防火墙失败"))


def get_create_apply_security_group_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreateSecurityGroupTask(),
             UpdatePortSecurityGroupTask(),
             PersistentPortSecurityGroup()
    )
    return flow

class SecurityGroupCreateApplyBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(SecurityGroupCreateApplyBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_create_apply_security_group_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        reservations = QUOTAS.reserve(self.context,
                                      **{'firewalls': 1}
        )
        try:
            sg = managers.security_groups.create(self.context.user_id, **kwargs)
        except Exception as err:
            LOG.info("Create security group: %s." % err)
            QUOTAS.rollback(self.context, reservations)
            raise err
        else:
            QUOTAS.commit(self.context, reservations)

        return sg

    def associate_resource_with_job(self, resource, job):
        managers.security_groups.update(self.context, resource.id, job_id=job.id)



