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
ACTION = 'nat:delete'


class DeleteNatTask(task.NebulaTask):

    default_provides = 'deleted_nat'

    def __init__(self):
        super(DeleteNatTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, nat_uuid, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除网络映射"))
        self.update_job_state_desc(job_id, _(u"开始删除底层资源"))

        get_neutron_client().delete_virtualrouter_nat(nat_uuid)
        self.update_job_state_desc(job_id, _(u"删除底层资源成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"删除网络映射失败"))
        # 失败不需要回滚


class PersistentNat(task.NebulaTask):

    def __init__(self):
        super(PersistentNat, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, nat_id, virtualrouter_floatingip_id, intern_ip, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除数据库记录"))
        managers.virtualruoter_nats.delete(self.admin_context, nat_id)
        if managers.virtualruoter_nats.get_by(self.admin_context, floatingip_id=virtualrouter_floatingip_id) is None:
            managers.virtualrouter_floatingips.update(self.admin_context, virtualrouter_floatingip_id,
                                                  dict(virtualrouter_id=None,
                                                       fixed_ip_address=None,
                                                       status=None)
                                                )

        self.update_job_state_desc(job_id, _(u"删除数据库记录成功"))
        self.update_job_state_desc(job_id, _(u"删除网络映射成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"删除数据库记录失败"))

def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeleteNatTask(), PersistentNat())
    return flow


class NatDeleteBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None, **kwargs):
        super(NatDeleteBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        nat = managers.virtualruoter_nats.get(
            self.context,
            kwargs['resource_id']
        )

        self.store.update(dict(
            nat_uuid=nat.virtualrouter_nat_uuid,
            nat_id=kwargs['resource_id'],
            intern_ip=nat.dest_ip,
            virtualrouter_floatingip_id=nat.floatingip.id
        ))
        return nat.floatingip.virtualrouter

    def associate_resource_with_job(self, resource, job):
        managers.virtualrouters.update(self.context, resource.id, dict(job_id=job.id))
