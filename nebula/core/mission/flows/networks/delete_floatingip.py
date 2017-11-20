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
ACTION = "virtualrouter_floatingip:delete"


class DeleteVirtualrouterFloatingIPTask(task.NebulaTask):

    default_provides = 'floating_ip'

    def __init__(self):
        super(DeleteVirtualrouterFloatingIPTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, floatingip_uuid, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除浮动IP"))
        self.update_job_state_desc(job_id, _(u"申请删除浮动IP"))

        vn = managers.virtualrouter_floatingips.get(self.admin_context, resource_id)
        if vn.virtualrouter:
            self.update_job_state_desc(job_id, _(u"浮动IP已经绑定了虚机"))
            raise ValueError

        get_neutron_client().delete_floatingip(floatingip=floatingip_uuid)

        self.update_job_state_desc(job_id, _(u"删除浮动IP成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"删除浮动IP失败"))


class DeleteVirtualrouterFloatingIPEntryTask(task.NebulaTask):
    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除浮动IP"))
        managers.virtualrouter_floatingips.delete(resource_id)
        self.update_job_state_desc(job_id, _(u"删除浮动IP成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"删除失败"))


def get_delete_virtualrouter_floatingip_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeleteVirtualrouterFloatingIPTask(),
             DeleteVirtualrouterFloatingIPEntryTask()
    )
    return flow


class VirtualrouterFloatingIPDeleteBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(VirtualrouterFloatingIPDeleteBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_delete_virtualrouter_floatingip_flow
        )

    def prepare_resource(self, *args, **kwargs):

        self.store.update(kwargs)
        vn = managers.virtualrouter_floatingips.get(self.context, kwargs['floatingip_id'])
        self.store['floatingip_uuid'] = vn.floatingip_uuid

        return vn

    def associate_resource_with_job(self, resource, job):
        managers.virtualrouter_floatingips.update(self.context, resource.id, dict(job_id=job.id))
