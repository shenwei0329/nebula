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
ACTION = "security_group:update"


class UpdateSecurityGroupTask(task.NebulaTask):

    default_provides = 'security_group'

    def __init__(self):
        super(UpdateSecurityGroupTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, security_group_uuid, name, description, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更新虚拟防火墙"))
        self.update_job_state_desc(job_id, _(u"申请更新虚拟防火墙资源"))
        get_neutron_client().update_security_group(
            security_group_uuid,
            body={'security_group': dict(
                name=name,
                description=description
            )}
        )
        self.update_job_state_desc(job_id, _(u"更新虚拟防火墙成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新虚拟防火墙失败"))


class PersistentUpdateSecurityGroup(task.NebulaTask):

    default_provides = 'update_security_group'

    def __init__(self):
        super(PersistentUpdateSecurityGroup, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, security_group_uuid, name, description, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入数据库成功"))
        parmas = dict(
            name=name,
            description=description
        )
        managers.security_groups.update(self.admin_context, resource_id, **parmas)

        self.update_job_state_desc(job_id, _(u"更新虚拟防火墙成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"更新虚拟防火墙失败"))


def get_update_security_group_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(UpdateSecurityGroupTask(),
             PersistentUpdateSecurityGroup())
    return flow


class SecurityGroupUpdateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(SecurityGroupUpdateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_update_security_group_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        security_group_id = kwargs.pop("resource_id")
        sg = managers.security_groups.get(self.context, security_group_id)
        self.store = dict(
            security_group_uuid=sg.security_group_uuid,
            name=kwargs["name"],
            description=kwargs.get("description", sg.description)
        )
        return sg

    def associate_resource_with_job(self, resource, job):
        managers.security_groups.update(self.context, resource.id, job_id=job.id)
