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
ACTION = "virtualrouter_floatingip:create"


class CreateVirtualrouterFloatingIPTask(task.NebulaTask):

    default_provides = 'floating_ip'

    def __init__(self):
        super(CreateVirtualrouterFloatingIPTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, virtualrouter_uuid, subnet_uuid, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始断开私有子网"))
        self.update_job_state_desc(job_id, _(u"申请断开子网资源"))

        get_neutron_client().remove_interface_router(
            router= virtualrouter_uuid,
            body={'subnet_id': subnet_uuid}
        )
        self.update_job_state_desc(job_id, _(u"断开子网资源成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"断开子网资源失败"))


class CreateVirtualrouterFloatingIPEntryTask(task.NebulaTask):
    def execute(self, job_id, resource_id, **kwargs):
        # 删除数据库中私有网络绑定路由器
        self.update_job_state_desc(job_id, _(u"开始从数据库删除子网绑定路由器"))
        managers.virtualrouter_subnets.delete_by(id=resource_id)
        self.update_job_state_desc(job_id, _(u"断开路由器成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"断开路由器失败"))


def get_create_virtualrouter_floatingip_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreateVirtualrouterFloatingIPTask(),
             CreateVirtualrouterFloatingIPEntryTask()
    )
    return flow


class VirtualrouterFloatingIPCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(VirtualrouterFloatingIPCreateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_create_virtualrouter_floatingip_flow
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        vn = managers.virtualrouter_floatingips.get_by(self.context,
                                                       network_id=kwargs['network_id'])

        return vn

    def associate_resource_with_job(self, resource, job):
        managers.virtualrouter_subnets.update(self.context, resource.id)
