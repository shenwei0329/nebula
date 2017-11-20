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
from kombu.utils import uuid

QUOTAS = quota.QUOTAS
LOG = log.getLogger(__name__)
ACTION = "binding_private_subnet_to_virtualrouter:create"


class BindingPrivateNetworkTask(task.NebulaTask):

    default_provides = 'binding_private_subnet'

    def __init__(self):
        super(BindingPrivateNetworkTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, virtualrouter_uuid, subnet_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始绑定私有子网到虚拟路由器"))
        subnet = managers.subnets.get(self.admin_context, subnet_id)

        self.update_job_state_desc(job_id, _(u"申请绑定私有子网到虚拟路由器"))
        vn = get_neutron_client().add_interface_router(
            router=virtualrouter_uuid,
            body={'subnet_id': subnet.subnet_uuid}
        )
        self.update_job_state_desc(job_id, _(u"绑定私有子网到虚拟路由器成功"))
        return vn

    def revert(self, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        vn = kwargs['result']
        if self.is_current_task_ok(vn):
            get_neutron_client().remove_interface_router(
                router=vn['id'],
                body={'subnet_id': vn['subnet_id']}
            )

class PersistentVirtualrouterNetwork(task.NebulaTask):

    default_provides = 'persitent_virtualrouter_subnet'

    def __init__(self):
        super(PersistentVirtualrouterNetwork, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, binding_private_subnet,
                subnet_id, virtualrouter_id, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"私有子网绑定到虚拟路由器成功存入数据库"))

        request_context = self.get_request_context(**kwargs)
        managers.virtualrouter_subnets.create(
            user_id,
            subnet_id=subnet_id,
            virtualrouter_id=virtualrouter_id,
            virtualrouter_subnet_uuid=uuid()
        )
        self.update_job_state_desc(job_id, _(u"私有子网绑定到虚拟路由器成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"私有子网绑定到虚拟路由器失败"))


def get_binding_private_subnet_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(BindingPrivateNetworkTask(), PersistentVirtualrouterNetwork())
    return flow


class PrivateNetworkBindingVirtualrouterBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(PrivateNetworkBindingVirtualrouterBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_binding_private_subnet_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        self.store = kwargs
        virtualrouter = managers.virtualrouters.get(self.context, kwargs["virtualrouter_id"])
        self.store["virtualrouter_uuid"] = virtualrouter.virtualrouter_uuid
        self.store["user_id"] = virtualrouter.owner_id
        return virtualrouter

    def associate_resource_with_job(self, resource, job):
        managers.virtualrouters.update(self.context, resource.id, dict(job_id=job.id))
