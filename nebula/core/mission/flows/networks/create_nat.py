# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core import constants
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    neutron import get_client as get_neutron_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = 'nat:create'


class CreateNatTask(task.NebulaTask):

    default_provides = 'nat'

    def __init__(self):
        super(CreateNatTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, proto,
                dest_ip, floatingip, dest_port, router_uuid, src_port, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建网络映射"))
        params = dict(
            extern_ip=floatingip,
            intern_ip=dest_ip,
            proto=proto,
            router_id=router_uuid
        )

        if proto in (constants.NET_PROTOCOL_TCP,
                     constants.NET_PROTOCOL_UDP):
            params["intern_port"] = dest_port
            params["extern_port"] = src_port

        self.update_job_state_desc(job_id, _(u"申请网络映射资源"))
        LOG.info("create nat params: %s" % params)

        rv = get_neutron_client().create_virtualrouter_nat(**params)

        self.update_job_state_desc(job_id, _(u"申请网络映射资源成功"))

        return rv['dnat']

    def revert(self, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)

        nat = kwargs['result']
        if self.is_current_task_ok(nat):
            get_neutron_client().delete_virtualrouter_nat(nat['id'])


class PersistentNat(task.NebulaTask):

    def __init__(self):
        super(PersistentNat, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, nat, virtualrouter_floatingip_id,
                virtualrouter_id, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"写入数据库"))
        request_context = self.get_request_context(**kwargs)

        LOG.info("create nat openstack result: %s" % nat)

        if nat['proto'] in ['icmp', 'ip']:
            nat['intern_port'] = None
            nat['extern_port'] = None

        managers.virtualruoter_nats.create(
            user_id,
            floatingip_id=virtualrouter_floatingip_id,
            virtualrouter_nat_uuid=nat["id"],
            proto=nat['proto'],
            dest_ip=nat['intern_ip'],
            dest_port=nat['intern_port'],
            src_port=nat['extern_port']
        )

        managers.virtualrouter_floatingips.update(self.admin_context, virtualrouter_floatingip_id,
                                                  dict(virtualrouter_id=virtualrouter_id,
                                                       fixed_ip_address=nat['intern_ip'],
                                                       status='Active')
                                                )

        self.update_job_state_desc(job_id, _(u"写入数据库成功"))
        self.update_job_state_desc(job_id, _(u"创建网络映射成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"创建网络映射失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreateNatTask(), PersistentNat())
    return flow


class NatCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None, **kwargs):
        super(NatCreateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):

        vp = managers.virtualrouter_floatingips.get(self.context, kwargs['virtualrouter_floatingip_id'])
        self.store.update(kwargs)
        self.store["floatingip_uuid"] = vp.floatingip_uuid
        self.store["floatingip_id"] = vp.id
        self.store["user_id"] = vp.owner_id
        self.store['floatingip'] = vp.floating_ip_address

        vr = managers.virtualrouters.get(self.context, kwargs['virtualrouter_id'])
        self.store['router_uuid'] = vr.virtualrouter_uuid


        return vp

    def associate_resource_with_job(self, resource, job):
        managers.virtualrouter_floatingips.update(self.context, resource.id, dict(job_id=job.id))
