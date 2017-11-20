# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    nova import get_client as get_nova_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = 'aggregate:remove_host'


class RemoveAggregateHostTask(task.NebulaTask):

    default_provides = 'form_data'

    def __init__(self):
        super(RemoveAggregateHostTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, aggregate_id, host_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始从集群移除主机"))
        resource = managers.compute_nodes.get(self.admin_context, host_id)
        aggregate = managers.aggregates.get(self.admin_context, aggregate_id)

        self.update_job_state_desc(job_id, _(u"开始删除底层资源"))

        LOG.info("RemoveAggregateHostTask_1::::::::::::::")
        LOG.info(aggregate.aggregate_uuid)
        LOG.info(resource.hostname)
        try:
            get_nova_client().servers.remove_host_aggregate(
                aggregate.aggregate_uuid,
                resource.os_hostname
            )
            self.update_job_state_desc(job_id, _(u"删除底层资源成功"))
        except Exception, e:
            LOG.error(unicode(e.message))
            self.update_job_state_desc(job_id, _(u"删除底层资源异常"))


        self.update_job_state_desc(job_id, _(u"开始删除数据库记录"))
        params = {
            "aggregate_id": None,
            "aggregate_time": ""
        }
        managers.compute_nodes.update(self.admin_context, host_id, params)
        self.update_job_state_desc(job_id, _(u"从集群移除主机成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"从集群移除主机失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(RemoveAggregateHostTask())
    return flow


class AggregateRemoveHostBuilder(Builder):

    def __init__(self, context=None, resource_kwargs=None, **kwargs):
        super(AggregateRemoveHostBuilder, self).__init__(
            context=context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        return managers.aggregates.get(self.context, kwargs['resource_id'])

    def associate_resource_with_job(self, resource, job):
        pass
