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
ACTION = "port:update"


class UpdatePortTask(task.NebulaTask):

    default_provides = 'port'

    def __init__(self):
        super(UpdatePortTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, security_group_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更新网卡"))
        resource = managers.ports.get(self.admin_context, resource_id)
        security_group = managers.security_groups.get(self.admin_context,
                                                      security_group_id)

        security_groups = [security_group.security_group_uuid]
        for sg in resource.get_security_groups():
            security_groups.append(sg.security_group_uuid)
        security_groups = list(set(security_groups))

        LOG.info("update port security group params: %s" % security_groups)
        self.update_job_state_desc(job_id, _(u"申请更新网卡"))
        get_neutron_client().update_port(
            resource.port_uuid,
            body={'port': {'security_groups': security_groups}}
        )
        self.update_job_state_desc(job_id, _(u"网卡更新成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"网卡更新失败"))


class PersistentUpdatePort(task.NebulaTask):

    default_provides = 'persitent_update_port'

    def __init__(self):
        super(PersistentUpdatePort, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, port, security_group_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"应用虚拟防火墙开始存入数据库"))
        managers.ports.update(self.admin_context,
                              resource_id,
                              security_group_id=security_group_id)

        self.update_job_state_desc(job_id, _(u"应用虚拟防火墙存入数据库成功"))
        self.update_job_state_desc(job_id, _(u"应用虚拟防火墙成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"应用虚拟防火墙失败"))


def get_update_port_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        UpdatePortTask(),
        PersistentUpdatePort()
    )
    return flow


class PortUpdateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(PortUpdateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_update_port_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        port_id = kwargs.pop("port_id")
        port = managers.ports.get(self.context, port_id)

        self.store.update(dict(
            security_group_id=kwargs["resource_id"]
        ))

        return port

    def associate_resource_with_job(self, resource, job):
        managers.ports.update(self.context, resource.id, job_id=job.id)


class UpdateArrayPortTask(task.NebulaTask):

    default_provides = 'array_port'

    def __init__(self):
        super(UpdateArrayPortTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, sgroup_id, port_id, **kwargs):
        for portid in port_id:
            port = managers.ports.update(self.admin_context, portid,
                                         security_group_id=sgroup_id)
            self.update_job_state_desc(job_id, _(u"开始更新网卡"))
            resource = managers.ports.get(self.admin_context, portid)
            sgroup_uuid = managers.security_groups.get(self.admin_context,
                                                       sgroup_id)

            self.update_job_state_desc(job_id, _(u"申请更新网卡"))
            get_neutron_client().update_port(
                resource.port_uuid,
                body={'port': {'security_groups': [sgroup_uuid["security_group_uuid"]]}}
            )
            self.update_job_state_desc(job_id, _(u"更新网卡成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新网卡失败"))


def get_update_array_port_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(UpdateArrayPortTask())
    return flow


class PortArrayUpdateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(PortArrayUpdateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_update_array_port_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        return managers.security_groups.get(self.context,
                                            security_group_id=kwargs["sgroup_id"])

    def associate_resource_with_job(self, resource, job):
        managers.security_groups.update(self.context,
                                        resource.id, job_id=job.id)

