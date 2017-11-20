# -*- coding: utf-8 -*-

import datetime

from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients.\
    nova import get_client as get_nova_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = 'aggregate:add_host'


def now(fmt=u"%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.now().strftime(fmt)


class AddAggregateHostTask(task.NebulaTask):

    default_provides = 'form_data'

    def __init__(self):
        super(AddAggregateHostTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, aggregate_id, host_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始增加主机到集群"))

        resource = managers.compute_nodes.get(self.admin_context, host_id)
        aggregate = managers.aggregates.get(self.admin_context, aggregate_id)

        self.update_job_state_desc(job_id, _(u"开始向底层发起请求"))
        rv = get_nova_client().servers.add_host_aggregate(
            aggregate_id=aggregate.aggregate_uuid,
            host=resource.os_hostname
        )
        self.update_job_state_desc(job_id, _(u"结束向底层发起请求"))

        self.update_job_state_desc(job_id, _(u"增加主机到集群成功"))

        return {
            "aggregate_id": aggregate_id,
            "aggregate_time": now()
        }

    def revert(self, *args, **kwargs):
        LOG.error('%s, args: %s, kwargs: %s' % (self.default_provides, args, kwargs))
        LOG.error(kwargs['result'])


class PersistentAggregateHost(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentAggregateHost, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, form_data, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入数据库"))

        managers.compute_nodes.update(self.admin_context,
                                      resource_id,
                                      form_data)

        self.update_job_state_desc(job_id, _(u"存入数据库成功"))
        self.update_job_state_desc(job_id, _(u"主机加入集群成功"))

    def revert(self, job_id, *args, **kwargs):
        LOG.error('%s, args: %s, kwargs: %s' % (self.default_provides, args, kwargs))
        LOG.error(kwargs['result'])
        self.update_job_state_desc(job_id, _(u"主机加入集群失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(AddAggregateHostTask(), PersistentAggregateHost())
    return flow


class AggregateAddHostBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None, **kwargs):
        super(AggregateAddHostBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        return managers.compute_nodes.get(self.context, kwargs["host_id"])

    def associate_resource_with_job(self, resource, job):
        pass
