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
ACTION = "virtualrouter_floatingip:update"


class UpdateVirtualrouterFloatingIPTask(task.NebulaTask):

    default_provides = 'floatingip'

    def __init__(self):
        super(UpdateVirtualrouterFloatingIPTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更新浮动IP"))
        self.update_job_state_desc(job_id, _(u"申请更新浮动IP"))
        #Do Nothing
        self.update_job_state_desc(job_id, _(u"浮动IP更新成功"))


    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"浮动IP更新失败"))

class UpdateVirtualrouterFloatingIPEntryTask(task.NebulaTask):

    def execute(self, job_id, resource_id, floating_ip, owner_id, floating_network_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更新浮动IP"))

        '''
        vrouters = managers.virtualrouters.filter_by(owner_id=owner_id)
        for vr in vrouters:
            vrouter_nets = managers.virtualrouter_networks.filter_by(owner_id=owner_id,
                                                                     virtualrouter_id=vr.id,
                                                                     network_id=floating_network_id)
            print("##############vrouter_nets:%s", vrouter_nets)
            if None != vrouter_nets:
                managers.virtualrouter_floatingips.update(self.admin_context, resource_id,
                                                  dict(floating_ip_address=floating_ip, virtualrouter_id=vr.id))
                break

        print("#########owner_id:%s", owner_id)
        '''
        managers.virtualrouter_floatingips.update(self.admin_context, resource_id,
                                                  dict(floating_ip_address=floating_ip, owner_id=owner_id))

        self.update_job_state_desc(job_id, _(u"更新浮动IP成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"更新浮动IP失败"))


def get_update_virtualrouter_floatingip_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(UpdateVirtualrouterFloatingIPTask(),
             UpdateVirtualrouterFloatingIPEntryTask()
    )
    return flow


class VirtualrouterFloatingIPUpdateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(VirtualrouterFloatingIPUpdateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_update_virtualrouter_floatingip_flow
        )

    def prepare_resource(self, *args, **kwargs):
        rt = managers.virtualrouter_floatingips.get_by(self.context,
                                                       floating_ip_address=kwargs['floating_ip'])
        self.store.update(rt)
        self.store.update(kwargs)
        return rt

    def associate_resource_with_job(self, resource, job):
        managers.virtualrouter_floatingips.update(self.context, resource.id, dict(job_id=job.id))
