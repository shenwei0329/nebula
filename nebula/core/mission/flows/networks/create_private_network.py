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
ACTION = "private_network:create"


class CreatePrivateNetworkTask(task.NebulaTask):

    default_provides = 'private_network'

    def __init__(self):
        super(CreatePrivateNetworkTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建网络"))
        resource = managers.private_networks.get(self.admin_context, resource_id)

        self.update_job_state_desc(job_id, _(u"申请网络资源"))

        network_info = dict()
        if resource.network_type == 'vlan':
            network_info = {'network': {
                'name': resource.name,
                'provider:network_type': resource.network_type,
                'provider:physical_network': resource.physical_network,
                'provider:segmentation_id': resource.segmentation_id,
                'router:external': resource.external_net,
                'shared': resource.shared
            }
            }
        elif resource.network_type == 'vxlan':
            network_info = {'network': {
                'name': resource.name,
                'provider:network_type': resource.network_type,
                'shared': resource.shared
            }
            }
        elif resource.network_type == 'flat':
            network_info = {'network': {
                'name': resource.name,
                'provider:network_type': resource.network_type,
                'provider:physical_network': resource.physical_network,
                'shared': resource.shared
            }
            }
            
            
        LOG.info(">>> shenwei <<< Create network: %s." % network_info)

        rv = get_neutron_client().create_network(body=network_info)
        self.update_job_state_desc(job_id, _(u"申请网络资源成功"))

        return rv['network']

    def revert(self, job_id, resource_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        private_network = kwargs['result']

        if self.is_current_task_ok(private_network):
            get_neutron_client().delete_network(private_network['id'])

        self.update_job_state_desc(job_id, _(u"网络创建失败"))


class PersistentPrivateNetwork(task.NebulaTask):

    default_provides = 'persitent_network'

    def __init__(self):
        super(PersistentPrivateNetwork, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, private_network, external_net, network_type,  **kwargs):
        self.update_job_state_desc(job_id, _(u"网络开始存入数据库"))
        managers.private_networks.update(self.admin_context, resource_id, **{
            'network_uuid': private_network['id'],
            'status': 'active'
        })

        self.update_job_state_desc(job_id, _(u"网络存入数据库成功"))
        self.update_job_state_desc(job_id, _(u"网络创建成功"))

    def revert(self, job_id, resource_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"网络创建失败"))


def get_create_network_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreatePrivateNetworkTask(), PersistentPrivateNetwork())
    return flow


class PrivateNetworkCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(PrivateNetworkCreateBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_create_network_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        self.store = kwargs
        reservations = QUOTAS.reserve(self.context,
                                      **{'private_networks': 1}
        )

        try:
            nt = managers.private_networks.create(self.context.user_id, **kwargs)
        except Exception as err:
            LOG.info("Create private networks faild: %s." % err)
            QUOTAS.rollback(self.context, reservations)
            raise err
        else:
            QUOTAS.commit(self.context, reservations)
        self.store.update(
            external_net=kwargs['external_net']
        )

        #All external network should be shared for all users
        if kwargs['external_net']:
            kwargs['shared'] = True

        return nt

    def associate_resource_with_job(self, resource, job):
        managers.private_networks.update(self.context, resource.id, job_id=job.id)
