# -*- coding: utf-8 -*-
import re
from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    neutron import get_client as get_neutron_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = "subnet:delete"


class DeleteSubnetTask(task.NebulaTask):

    default_provides = 'subnet'

    def __init__(self):
        super(DeleteSubnetTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, subnet_id, subnet_uuid, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除子网"))
        resource = managers.subnets.get(self.admin_context, subnet_id)
        #判断网络是否有网卡未清除
        if len(resource.ports):
            message = u"子网存在正在使用的网卡，不能删除"
            self.update_job_state_desc(job_id, _(message))
            raise Exception(message)
        self.update_job_state_desc(job_id, _(u"申请删除子网资源"))
        try:
            get_neutron_client().delete_subnet(subnet_uuid)
        except Exception as err:
            error = str(err)
            self.update_job_state_desc(job_id, _(error))
            LOG.error(error)
            #if re.search(r'[\w|-]{36}|None\sdoes not exist', error):
            #    self.update_job_state_desc(job_id, _(u"子网已经被删除，可以忽略！"))
            #    pass
            #else:
            raise err
        self.update_job_state_desc(job_id, _(u"删除子网资源成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"删除子网资源失败"))


class DeleteSubnetEntryTask(task.NebulaTask):

    def execute(self, job_id, resource_id, subnet_id, **kwargs):
        # 删除数据库中私有网络
        self.update_job_state_desc(job_id, _(u"开始从数据库删除子网"))
        managers.subnets.delete_by(id=subnet_id)
        self.update_job_state_desc(job_id, _(u"删除子网成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"删除子网失败"))


def get_delete_subnet_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeleteSubnetTask(),
             DeleteSubnetEntryTask())
    return flow


class SubnetDeleteBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(SubnetDeleteBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_delete_subnet_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        subnet = managers.subnets.get(self.context, kwargs['resource_id'])
        self.store.update(dict(
            subnet_id=kwargs['resource_id'],
            subnet_uuid=subnet.subnet_uuid
        ))
        return subnet.network

    def associate_resource_with_job(self, resource, job):
        managers.private_networks.update(self.context, resource.id, job_id=job.id)

