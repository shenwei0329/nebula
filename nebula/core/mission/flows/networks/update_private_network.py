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
ACTION = "private_network:update"


class UpdatePrivateNetworkTask(task.NebulaTask):

    default_provides = 'private_network'

    def __init__(self):
        super(UpdatePrivateNetworkTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更新私有网络"))
        resource = managers.private_networks.get(self.admin_context, resource_id)

        self.update_job_state_desc(job_id, _(u"申请更新网络资源"))
        get_neutron_client().update_network(
            resource.network_uuid,
            body={'network': {'name': resource.name}}
        )
        self.update_job_state_desc(job_id, _(u"更新网络成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新网络失败"))


def get_update_network_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(UpdatePrivateNetworkTask())
    return flow


class PrivateNetworkUpdateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(PrivateNetworkUpdateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_update_network_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        private_network_id = kwargs.pop("resource_id")
        return managers.private_networks.update(self.context,
                                                private_network_id, **kwargs)

    def associate_resource_with_job(self, resource, job):
        managers.private_networks.update(self.context,
                                         resource.id, job_id=job.id)
