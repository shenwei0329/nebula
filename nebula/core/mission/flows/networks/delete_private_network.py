# -*- coding: utf-8 -*-
import re
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
ACTION = "private_network:delete"


class DeletePrivateNetworkTask(task.NebulaTask):

    default_provides = 'private_network'

    def __init__(self):
        super(DeletePrivateNetworkTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, user_id, **kwargs):
        
        LOG.info(">>> shenwei <<< Delete private networks." )

        self.update_job_state_desc(job_id, _(u"开始删除私有网络"))
        resource = managers.private_networks.get(self.admin_context, resource_id)
        #判断网络是否绑定路由器
        if len(resource.virtualrouter_networks):
            message = u"私有网络仍然绑定在路由器，不能删除"
            self.update_job_state_desc(job_id, _(message))
            raise Exception(message)
        #判断网络下是否存在子网
        if len(resource.subnets):
            message = u"私有网络存在可用子网，不能删除"
            self.update_job_state_desc(job_id, _(message))
            raise Exception(message)
        self.update_job_state_desc(job_id, _(u"申请删除网络资源"))
        if resource.network_uuid:
            try:
                get_neutron_client().delete_network(resource.network_uuid)
            except Exception as err:
                error = str(err)
                self.update_job_state_desc(job_id, _(error))
                if re.search(r'[\w|-]{36}|None\sdoes not exist', error):
                    self.update_job_state_desc(job_id, _(u"私有网络已经不存在"))
                    pass
                else:
                    raise err
        else:
            self.update_job_state_desc(job_id, _(u"不存在网络资源"))
        self.update_job_state_desc(job_id, _(u"删除网络资源成功"))

    def revert(self, job_id, user_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"删除网络资源失败"))


class DeletePrivateNetworkEntryTask(task.NebulaTask):
    def execute(self, job_id, user_id, resource_id, ext_network, **kwargs):
        # 删除数据库中私有网络
        self.update_job_state_desc(job_id, _(u"开始从数据库删除网络资源"))
        request_context = self.get_request_context(**kwargs)
        reservations = QUOTAS.reserve(
            request_context,
            user_id=user_id,
            **{'private_networks': -1}
        )
        try:
            managers.private_networks.delete_by(id=resource_id)
        except Exception as err:
            self.update_job_state_desc(job_id, _(u"数据库删除私有网络失败"))
            QUOTAS.rollback(request_context, reservations, user_id=user_id)
            raise err
        else:
            QUOTAS.commit(self.get_request_context(**kwargs), reservations, user_id=user_id)

        self.update_job_state_desc(job_id, _(u"删除私有网络成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"从数据库删除网络资源失败"))


def get_delete_network_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeletePrivateNetworkTask(), DeletePrivateNetworkEntryTask())
    return flow


class PrivateNetworkDeleteBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(PrivateNetworkDeleteBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_delete_network_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        resource = managers.private_networks.get(self.context, kwargs['resource_id'])
        self.store.update(
            user_id=resource.owner_id,
            ext_network=resource.external_net
        )
        return resource

    def associate_resource_with_job(self, resource, job):
        managers.private_networks.update(self.context, resource.id, job_id=job.id)
