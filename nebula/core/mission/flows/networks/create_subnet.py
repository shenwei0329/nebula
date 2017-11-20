# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow
import json

from nebula.core import constants
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    neutron import get_client as get_neutron_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = "subnet:create"


class CreateSubnetTask(task.NebulaTask):

    default_provides = 'subnet'

    def __init__(self):
        super(CreateSubnetTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, network_uuid, name, cidr,
                cidr_value, gateway_ip, dns_nameservers, allocation_pools,
                host_routes, description, user_id, enable_dhcp, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建私子网"))

        cidr = "/".join([cidr, str(cidr_value)])
        params = dict(network_id=network_uuid,
                      name=name,
                      cidr=cidr,
                      ip_version=constants.IPv4,
                      enable_dhcp=enable_dhcp)

        if gateway_ip:
            params["gateway_ip"] = gateway_ip

        if dns_nameservers:
            params["dns_nameservers"] = [dns_nameservers, ]

        if allocation_pools:
            format_allocation_pools = list()
            for ips in allocation_pools.split(","):
                ips = ips.split("_")
                if ips:
                    ip = dict(start=ips[0],
                              end=ips[1])
                    format_allocation_pools.append(ip)
            params["allocation_pools"] = format_allocation_pools

        if host_routes:
            format_host_routes = list()
            for routers in host_routes.split(","):
                routers = routers.split("_")
                if routers:
                    router = dict(nexthop=routers[0],
                                  destination=routers[1])
                    format_host_routes.append(router)
            params["host_routes"] = format_host_routes

        self.update_job_state_desc(job_id, _(u"申请子网资源"))
        LOG.info("create subnet params: %s" % params)

        subnet = get_neutron_client().create_subnet(
            body={'subnet': params}
        )
        self.update_job_state_desc(job_id, _(u"申请子网资源成功"))

        return subnet['subnet']

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"申请子网资源失败"))
        subnet = kwargs['result']
        if self.is_current_task_ok(subnet):
            get_neutron_client().delete_subnet(subnet['id'])


class PersistentSubnet(task.NebulaTask):

    default_provides = 'persitent_subnet'

    def __init__(self):
        super(PersistentSubnet, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, subnet, description, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"子网创建成功存入数据库"))
        LOG.info("create subnet openstack return: %s" % subnet)

        managers.subnets.create(
            user_id,
            network_id=resource_id,
            subnet_uuid=subnet['id'],
            name=subnet["name"],
            cidr=subnet["cidr"],
            gateway_ip=subnet["gateway_ip"],
            dns_nameservers=subnet["dns_nameservers"],
            allocation_pools=subnet["allocation_pools"],
            host_routes=subnet["host_routes"],
            description=description,
            enable_dhcp=subnet['enable_dhcp']
        )
        self.update_job_state_desc(job_id, _(u"子网存入数据库成功"))
        self.update_job_state_desc(job_id, _(u"创建子网成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"创建子网失败"))


def get_create_subnet_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreateSubnetTask(),
             PersistentSubnet())
    return flow


class SubnetCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(SubnetCreateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_create_subnet_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        net = managers.private_networks.get(self.context, kwargs["private_network_id"])
        if net.external_net:
            self.store['enable_dhcp'] = False
        else:
            self.store['enable_dhcp'] = True
        self.store.update(kwargs)
        self.store["network_uuid"] = net.network_uuid
        self.store["user_id"] = net.owner_id
        return net

    def associate_resource_with_job(self, resource, job):
        managers.private_networks.update(self.context, resource.id, job_id=job.id)
