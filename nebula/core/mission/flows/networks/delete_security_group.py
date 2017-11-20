# -*- coding: utf-8 -*-
import re
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
ACTION = "security_group:delete"


class DeleteSecurityGroupTask(task.NebulaTask):

    default_provides = 'security_group'

    def __init__(self):
        super(DeleteSecurityGroupTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除虚拟防火墙"))
        resource = managers.security_groups.get(self.admin_context, resource_id)
        self.update_job_state_desc(job_id, _(u"申请删除虚拟防火墙资源"))
        try:
            get_neutron_client().delete_security_group(resource.security_group_uuid)
        except Exception as err:
            error = str(err)
            if re.search(r'[\w|-]{36}|None\sdoes not exist', error):
                self.update_job_state_desc(job_id, _(u"虚拟防火墙资源已不存在！"))
                pass
            else:
                self.update_job_state_desc(job_id, _(error))
                raise err
        self.update_job_state_desc(job_id, _(u"删除虚拟防火墙资源成功"))

    def revert(self, job_id, user_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"删除虚拟防火墙资源失败"))


class DeleteSecurityGroupRuleEntryTask(task.NebulaTask):
    def execute(self, job_id, resource_id, **kwargs):
        # 先删除数据库该虚拟防火墙所有虚拟防火墙规则
        self.update_job_state_desc(job_id, _(u"开始从数据库删除虚拟防火墙规则"))
        security_group = managers.security_groups.get(self.admin_context,
                                                      resource_id)
        managers.security_group_rules.delete_by(security_group_id=security_group.id)
        self.update_job_state_desc(job_id, _(u"删除虚拟防火墙规则成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"从数据库删除虚拟防火墙对应虚拟防火墙规则失败"))


class DeleteSecurityGroupEntryTask(task.NebulaTask):
    def execute(self, job_id, resource_id, user_id, **kwargs):
        # 先删除数据库该虚拟防火墙所有虚拟防火墙规则
        self.update_job_state_desc(job_id, _(u"开始从数据库删除虚拟防火墙"))
        reservations = QUOTAS.reserve(
            self.get_request_context(**kwargs),
            user_id=user_id,
            **{'firewalls': -1}
        )
        try:
            managers.security_groups.delete_by(id=resource_id)
        except Exception as err:
            self.update_job_state_desc(job_id, _(u"数据库删除虚拟防火墙失败"))
            QUOTAS.rollback(self.get_request_context(**kwargs), reservations, user_id=user_id)
            raise err
        else:
            QUOTAS.commit(self.get_request_context(**kwargs), reservations, user_id=user_id)

        self.update_job_state_desc(job_id, _(u"删除虚拟防火墙成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"从数据库删除虚拟防火墙失败"))


def get_delete_security_group_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeleteSecurityGroupTask(),
             DeleteSecurityGroupRuleEntryTask(),
             DeleteSecurityGroupEntryTask())
    return flow


class SecurityGroupDeleteBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(SecurityGroupDeleteBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_delete_security_group_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        resource = managers.security_groups.get(self.context, kwargs['resource_id'])
        self.store.update(
            user_id=resource.owner_id,
        )
        return resource

    def associate_resource_with_job(self, resource, job):
        managers.security_groups.update(self.context, resource.id, job_id=job.id)


class DeleteSecurityGroupArrayTask(task.NebulaTask):

    default_provides = 'r_security_group'

    def __init__(self):
        super(DeleteSecurityGroupArrayTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, sgroup_id, port_id, **kwargs):
        for src in sgroup_id:
            self.update_job_state_desc(job_id, _(u"开始卸载虚拟防火墙"))

            managers.ports.detach_by_security_group(self.admin_context, port_id, security_group_id=src)
            sgroup_uuid = managers.security_groups.except_by(sgroup_id=src, port_id=port_id)

            port = managers.ports.get(self.admin_context, port_id)
            self.update_job_state_desc(job_id, _(u"申请卸载虚拟防火墙资源"))

            s_list = []
            for i in sgroup_uuid:
                s_list.append(i.security_group_uuid)

            get_neutron_client().update_port(
                port.port_uuid,
                body={'port': {
                    'security_groups': s_list
                    }
                }
            )
            self.update_job_state_desc(job_id, _(u"卸载虚拟防火墙资源成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"卸载虚拟防火墙资源失败"))


class DeleteSecurityGroupArrayRuleEntryTask(task.NebulaTask):
    def execute(self, job_id, resource_id, **kwargs):
        # 先删除数据库该虚拟防火墙所有虚拟防火墙规则
        for src in resource_id:
            self.update_job_state_desc(job_id, _(u"开始从数据库删除虚拟防火墙对应虚拟防火墙规则"))
            security_group = managers.security_groups.get(self.admin_context, src)
            managers.security_group_rules.delete_by(security_group_id=security_group.id)
            self.update_job_state_desc(job_id, _(u"从数据库删除虚拟防火墙对应虚拟防火墙规则成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"从数据库删除虚拟防火墙对应虚拟防火墙规则失败"))


class DeleteSecurityGroupArrayEntryTask(task.NebulaTask):
    def execute(self, job_id, resource_id, **kwargs):
        # 先删除数据库该虚拟防火墙所有虚拟防火墙规则
        for src in resource_id:
            self.update_job_state_desc(job_id, _(u"开始从数据库删除虚拟防火墙"))
            managers.security_groups.delete_by(id=src)
            self.update_job_state_desc(job_id, _(u"删除虚拟防火墙规则成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"从数据库删除虚拟防火墙失败"))


def get_delete_security_group_array_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeleteSecurityGroupArrayTask()
    )
    return flow


class SecurityGroupArrayDeleteBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(SecurityGroupArrayDeleteBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_delete_security_group_array_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        return managers.ports.get(self.context, kwargs["port_id"])

    def associate_resource_with_job(self, resource, job):
        managers.ports.update(self.context, resource.id, job_id=job.id)


class DetachSecurityGroupTask(task.NebulaTask):
    default_provides = 'detach_security_group'

    def __init__(self):
        super(DetachSecurityGroupTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, sgroup_id, port_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始卸载虚拟防火墙"))

        managers.ports.detach_by_security_group(self.admin_context, port_id, security_group_id=sgroup_id)
        # select all security groups as to (port_id & !sgroup_id)
        sgroup_uuid = managers.security_groups.except_by(sgroup_id=sgroup_id, port_id=port_id)
        port = managers.ports.get(self.admin_context, port_id)
        self.update_job_state_desc(job_id, _(u"申请卸载虚拟防火墙"))

        s_list = []
        if sgroup_uuid:
            for i in sgroup_uuid:
                s_list.append(i.security_group_uuid)

        get_neutron_client().update_port(
            port.port_uuid,
            body={'port': {
                'security_groups': s_list
                }
            }
        )
        self.update_job_state_desc(job_id, _(u"卸载虚拟防火墙成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"卸载虚拟防火墙失败"))


def detach_security_group_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DetachSecurityGroupTask()
    )
    return flow


class DetachSecurityGroupBuilder(Builder):
    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(DetachSecurityGroupBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=detach_security_group_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        return managers.ports.get(self.context, kwargs["port_id"])

    def associate_resource_with_job(self, resource, job):
        managers.ports.update(self.context, resource.id, job_id=job.id)
