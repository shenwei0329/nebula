# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core import constants
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients.nova import get_client as get_nova_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = 'host:remove_aggregate'


class RemoveAggregateTask(task.NebulaTask):
    default_provides = 'host'

    def __init__(self):
        super(RemoveAggregateTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"验证主机资源"))
        host = managers.compute_nodes.get(self.admin_context, resource_id)

        LOG.info("========%s,%s,%s", resource_id, kwargs, host)

        self.update_job_state_desc(job_id, _(u"主机资源删除中"))
        get_nova_client().servers.\
            remove_host_aggregate(host.aggregate.aggregate_uuid,
                                  host.os_hostname)

        self.update_job_state_desc(job_id, _(u"更新数据库记录"))
        managers.compute_nodes.update(self.admin_context,
                                      resource_id,
                                      {'aggregate_id': None})  # 清楚集群ID

        self.update_job_state_desc(job_id, _(u"主机从集群移除成功"))

    def revert(self, job_id,*args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        rv = kwargs['result']
        #回滚
        if self.is_current_task_ok(rv):
            #get_nova_client().servers.check_disable_compute_node(host['hostname'])
            #get_nova_client().servers.add_host_aggregate(rv.aggregate.aggregate_uuid, host.os_hostname)
            LOG.info("========@@@@@@@@@")
            pass
        else:
            self.update_job_state_desc(job_id, _(u"移除集群失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(RemoveAggregateTask())
    return flow


class RemoveAggregateBuilder(Builder):

    def __init__(self, context, resource_args=(),
                 resource_kwargs=None, **kwargs):

        super(RemoveAggregateBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        return managers.compute_nodes.get(self.context, kwargs['resource_id'])

    def associate_resource_with_job(self, resource, job):
        managers.compute_nodes.update(self.context,
                                      resource.id,
                                      dict(job_id=job.id))
