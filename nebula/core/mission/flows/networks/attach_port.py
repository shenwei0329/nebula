# -*- coding: utf-8 -*-
import re
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
ACTION = "port:attach"


class DetachPortTask(task.NebulaTask):

    default_provides = 'r_detach_port'

    def __init__(self):
        super(DetachPortTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始卸载网卡"))
        resource = managers.ports.get(self.admin_context, resource_id)
        try:
            get_nova_client().servers.interface_detach(
                resource.instance.instance_uuid,
                resource.port_uuid
            )
        except Exception as err:
            error = str(err)
            self.update_job_state_desc(job_id, _(error))
            if re.search(r'[\w|-]{36}|None\sdoes not exist', error) or resource.port_uuid:
                self.update_job_state_desc(job_id, _(u"虚拟防火墙已经被删除，可以忽略！"))
                pass
            else:
                raise err
        self.update_job_state_desc(job_id, _(u"卸载网卡资源成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"卸载网卡资源失败"))


class DeletePortEntryTask(task.NebulaTask):

    def execute(self, job_id, resource_id, **kwargs):
        # 删除数据库中私有网络
        self.update_job_state_desc(job_id, _(u"开始删除数据库网卡"))
        managers.ports.delete(resource_id)
        self.update_job_state_desc(job_id, _(u"从数据库删除网卡成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"从数据库删除网卡失败"))


class InstanceCreatePortTask(task.NebulaTask):

    default_provides = 'port'

    def __init__(self):
        super(InstanceCreatePortTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, port_id, mac_addr, upper_limit, floor_limit, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建网卡"))
        resource = managers.ports.get(self.admin_context, port_id)

        self.update_job_state_desc(job_id, _(u"申请网卡资源"))

        port_param = {}
        if mac_addr:
            port_param['mac_address'] = mac_addr

        port_param['name'] = resource.name
        port_param['network_id'] = resource.network.network_uuid
        port_param['fixed_ips'] = resource.fixed_ips
        port_param['bandwidth_tx'] = upper_limit
        port_param['bandwidth_rx'] = floor_limit

        port = get_neutron_client().create_port(
            body={'port': port_param
            }
        )
        self.update_job_state_desc(job_id, _(u"网卡资源申请成功"))

        return port['port']

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"挂载网卡失败"))
        self.log_current_task_failures(*args, **kwargs)
        managers.ports.delete(kwargs['port_id'])
        get_neutron_client().delete_port(kwargs['port_id'])



class InstanceAttachPortTask(task.NebulaTask):

    default_provides = 'attach_port'

    def __init__(self):
        super(InstanceAttachPortTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, instance_id, port, **kwargs):
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
        self.update_job_state_desc(job_id, _(u"挂载网卡失败"))


class InstanceApplySecurityGroupTask(task.NebulaTask):

    default_provides = 'r_security_group'

    def __init__(self):
        super(InstanceApplySecurityGroupTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, port, sgroup_id, **kwargs):
        sgroup_list = []
        if sgroup_id:
            self.update_job_state_desc(job_id, _(u"开始应用虚拟防火墙"))
            self.update_job_state_desc(job_id, _(u"申请应用虚拟防火墙"))
            sgroup_uuid = managers.security_groups.get(self.admin_context, sgroup_id)

            if sgroup_uuid:
                sgroup_list.append(sgroup_uuid["security_group_uuid"])

        updated_port = get_neutron_client().update_port(
            port["id"],
            body={'port': {
                'security_groups': sgroup_list,
                }
            }
        )

        if sgroup_id:
            self.update_job_state_desc(job_id, _(u"应用虚拟防火墙成功"))
        return updated_port

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"应用虚拟防火墙失败"))


class PersistentSGP(task.NebulaTask):

    default_provides = 'r_security_group_port'

    def __init__(self):
        super(PersistentSGP, self).__init__(addons=[ACTION])

    def execute(self, job_id, port_id, r_security_group, sgroup_id, **kwargs):

        managers.ports.update(self.admin_context, port_id, **{
            'port_uuid': r_security_group['port']['id'],
            'fixed_ips': r_security_group['port']['fixed_ips'],
            'mac_address': r_security_group['port']['mac_address'],
            'bandwidth_rx': r_security_group['port']['bandwidth_rx'],
            'bandwidth_tx': r_security_group['port']['bandwidth_rx'],
            'status': constants.PORT_STATUS_ACTIVE
        })

        if sgroup_id:
            self.update_job_state_desc(job_id, _(u"应用虚拟防火墙开始存入数据库"))
            managers.ports.update(self.admin_context, port_id, security_group_id=sgroup_id)
        self.update_job_state_desc(job_id, _(u"挂载网卡成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"应用虚拟防火墙入库失败"))


def get_attach_port_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        InstanceCreatePortTask(),
        InstanceAttachPortTask(),
        InstanceApplySecurityGroupTask(),
        PersistentSGP()
    )
    return flow


class PortAttachBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(PortAttachBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_attach_port_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        instance = managers.instances.get(self.context, kwargs.get('instance_id'))
        port = managers.ports.create(instance.owner_id,
                                     **kwargs
        )
        self.store.update(port_id=port.id)
        self.store.update(kwargs)
        return instance

    def associate_resource_with_job(self, resource, job):
        managers.instances.update(self.context,
                                  resource.id, dict(job_id=job.id))

