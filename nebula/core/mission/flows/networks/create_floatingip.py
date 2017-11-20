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
ACTION = "virtualrouter_floatingip:create"


class CreateVirtualrouterFloatingIPTask(task.NebulaTask):

    default_provides = 'floating_ip'

    def __init__(self):
        super(CreateVirtualrouterFloatingIPTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, network_id, network_uuid, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始分配浮动IP"))
        self.update_job_state_desc(job_id, _(u"申请分配浮动IP"))

        rt = get_neutron_client().create_floatingip(
            body={"floatingip": {"floating_network_id": network_uuid}}
        )

        self.update_job_state_desc(job_id, _(u"分配浮动IP成功"))
        rt['floatingip']['network_id'] = network_id
        rt['floatingip']['user_id'] = user_id

        return rt['floatingip']

    def revert(self, job_id, resource_id, *args, **kwargs):
        managers.virtualrouter_floatingips.delete(resource_id)
        self.update_job_state_desc(job_id, _(u"分配浮动IP失败"))

class CreateVirtualrouterFloatingIPEntryTask(task.NebulaTask):

    def execute(self, job_id, resource_id, floating_ip, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始保存浮动IP到数据库"))

        managers.virtualrouter_floatingips.update(self.admin_context, resource_id, dict(
                                                      floatingip_uuid=floating_ip['id'],
                                                      floating_ip_address=floating_ip['floating_ip_address'],
                                                      floating_network_id=floating_ip['network_id'],
                                                      virtualrouter_id=floating_ip['router_id'])
                                                    )

        self.update_job_state_desc(job_id, _(u"分配浮动IP成功"))

    def revert(self, job_id, resource_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        rt = kwargs['result']
        get_neutron_client().delete_floatingip(rt['id'])
        managers.virtualrouter_floatingips.delete(resource_id)
        self.update_job_state_desc(job_id, _(u"分配浮动IP失败"))


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
        vn = managers.private_networks.get(self.context, kwargs['network_id'])
        rt = managers.virtualrouter_floatingips.create(
                                        uuid=uuid(),
                                        creator_id =vn.owner.id,
                                        floating_ip='--',
                                        floating_network_id=kwargs['network_id'],
                                        fixed_ip=None,
                                        virtualrouter_id=None
        )

        self.store['network_uuid'] = vn.network_uuid
        self.store['user_id'] = vn.owner.id
        self.store['seq_id'] = vn.id

        return rt

    def associate_resource_with_job(self, resource, job):
        managers.virtualrouter_floatingips.update(self.context, resource.id, dict(job_id=job.id))
