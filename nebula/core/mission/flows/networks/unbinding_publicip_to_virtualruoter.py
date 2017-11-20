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
ACTION = "unbinding_network_to_virtualrouter"


class UnbindingPublicIPTask(task.NebulaTask):

    default_provides = 'unbinding'

    def __init__(self):
        super(UnbindingPublicIPTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, virtualrouter_uuid, network_uuid, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始清除虚拟路由器网关"))

        self.update_job_state_desc(job_id, _(u"开始删除底层资源"))
        router_info = {"router": {"external_gateway_info": {}}}
        rv = get_neutron_client().update_router(router=virtualrouter_uuid, body=router_info)

        self.update_job_state_desc(job_id, _(u"删除底层资源成功"))

        return rv

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"清除虚拟路由器网关失败"))
        # 未删除成功不需要回滚


class PersistenPublicIPUnbindingTask(task.NebulaTask):

    default_provides = 'unbinding_record'

    def __init__(self):
        super(PersistenPublicIPUnbindingTask, self).__init__(addons=[ACTION])

    def execute(self,  job_id, resource_id, user_id, network_id, virtualrouter_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更新数据库"))
        managers.virtualrouter_networks.delete_by(id=resource_id)
        #managers.virtualrouter_floatingips.update_router(self.admin_context, network_id, user_id, None)
        self.update_job_state_desc(job_id, _(u"更新数据库成功"))
        self.update_job_state_desc(job_id, _(u"清除虚拟路由器网关成功"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(UnbindingPublicIPTask(), PersistenPublicIPUnbindingTask())
    return flow


class UnbindingPublicIPBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(UnbindingPublicIPBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        net = managers.private_networks.get(self.context, kwargs['network_id'])
        vr = managers.virtualrouters.get(self.context, kwargs['virtualrouter_id'])
        vn = managers.virtualrouter_networks.get(self.context, kwargs['resource_id'])

        self.store.update(kwargs)
        self.store['network_uuid']=net.network_uuid
        self.store['virtualrouter_uuid']=vr['virtualrouter_uuid']
        self.store["user_id"] = vr.owner_id

        return vn

    def associate_resource_with_job(self, resource, job):
         managers.virtualrouter_networks.update(self.context, resource.id, job_id=job.id)
