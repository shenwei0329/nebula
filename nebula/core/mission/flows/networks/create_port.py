# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow
from nebula.core import constants

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    nova import get_client as get_nova_client
from nebula.core.openstack_clients.neutron import \
    get_client as get_neutron_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = "port:create"


class CreatePortTask(task.NebulaTask):

    default_provides = 'port'

    def __init__(self):
        super(CreatePortTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, port_id, network_uuid, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建网卡"))
        resource = managers.ports.get(self.admin_context, port_id)

        self.update_job_state_desc(job_id, _(u"申请创建网卡"))
        port = get_neutron_client().create_port(
            body={'port': {
                'name': resource.name,
                'network_id': network_uuid,
                'fixed_ips': resource.fixed_ips
                }
            }
        )
        self.update_job_state_desc(job_id, _(u"创建网卡成功"))

        return port['port']

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        port = kwargs['result']
        if self.is_current_task_ok(port):
            managers.ports.delete(kwargs["port_id"])
            get_neutron_client().delete_port(port['id'])
        self.update_job_state_desc(job_id, _(u"创建网卡失败"))


class AttachPortTask(task.NebulaTask):

    default_provides = 'attach_port'

    def __init__(self):
        super(AttachPortTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, instance_id, port, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始挂载网卡"))
        self.update_job_state_desc(job_id, _(u"申请挂载网卡"))
        instance = managers.instances.get(self.admin_context, instance_id)
        get_nova_client().servers.interface_attach_v1_1(
            instance.instance_uuid,
            port["id"]
        )
        self.update_job_state_desc(job_id, _(u"挂载网卡成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"申请挂载网卡失败"))


class PersistentPort(task.NebulaTask):

    default_provides = 'persitent_port'

    def __init__(self):
        super(PersistentPort, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, port_id, port, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始存入数据卷"))
        managers.ports.update(self.admin_context, port_id, **{
            'port_uuid': port['id'],
            'fixed_ips': port['fixed_ips'],
            'mac_address': port['mac_address'],
            'status': constants.PORT_STATUS_ACTIVE
        })
        self.update_job_state_desc(job_id, _(u"接入虚拟机成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"接入虚拟机失败"))


def get_create_port_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        CreatePortTask(),
        AttachPortTask(),
        PersistentPort()
    )
    return flow


class PortCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(PortCreateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_create_port_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        net = managers.private_networks.get(self.context, kwargs["network_id"])
        port = managers.ports.create(net.owner_id, **kwargs)
        self.store["port_id"] = port.id
        self.store["network_uuid"] = net.network_uuid
        return net

    def associate_resource_with_job(self, resource, job):
        managers.private_networks.update(self.context, resource.id, job_id=job.id)
