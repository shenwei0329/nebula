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
ACTION = "binding_externalnetwork_to_virtualrouter"

class BindingExternalNetworkTask(task.NebulaTask):

    default_provides = 'binding_external_network'

    def __init__(self):
        super(BindingExternalNetworkTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, virtualrouter_uuid, network_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始设置虚拟路由器网关"))
        net = managers.private_networks.get(self.admin_context, network_id)
        self.update_job_state_desc(job_id, _(u"申请设置虚拟路由器网关"))

        router_info = {"router":{"external_gateway_info":{"network_id": net.network_uuid}}}
        vn = get_neutron_client().update_router(router=virtualrouter_uuid ,body=router_info)
        self.update_job_state_desc(job_id, _(u"设置虚拟路由器网关成功"))

        return vn['router']

    def revert(self, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        vn = kwargs['result']
        if self.is_current_task_ok(vn):
            router_info = {"router": {"external_gateway_info": {}}}
            get_neutron_client().update_router(router=kwargs['virtualrouter_uuid'], body=router_info)


class PersistentVirtualrouterNetwork(task.NebulaTask):

    default_provides = 'persitent_virtualrouter_network'

    def __init__(self):
        super(PersistentVirtualrouterNetwork, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, binding_external_network,
                network_id, virtualrouter_id, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"虚拟路由器网关成功存入数据库"))
        managers.virtualrouter_networks.create(
            user_id,
            network_id=network_id,
            virtualrouter_id=virtualrouter_id,
            virtualrouter_network_uuid=binding_external_network['id']
        )
       # managers.virtualrouter_floatingips.update_router(self.admin_context, network_id, user_id, virtualrouter_id)

        self.update_job_state_desc(job_id, _(u"设置虚拟路由器网关成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"设置虚拟路由器网关失败"))


def get_binding_external_network_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(BindingExternalNetworkTask(), PersistentVirtualrouterNetwork())
    return flow


class BindingPublicIPBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(BindingPublicIPBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_binding_external_network_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        self.store = kwargs
        virtualrouter = managers.virtualrouters.get(self.context, kwargs["virtualrouter_id"])
        self.store["virtualrouter_uuid"] = virtualrouter.virtualrouter_uuid
        self.store["user_id"] = virtualrouter.owner_id
        return virtualrouter

    def associate_resource_with_job(self, resource, job):
        managers.virtualrouters.update(self.context, resource.id, dict(job_id=job.id))
