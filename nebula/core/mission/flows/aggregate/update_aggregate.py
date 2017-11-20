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
ACTION = 'aggregate:update'


class UpdateAggregateTask(task.NebulaTask):

    default_provides = 'callapi'

    def __init__(self):
        super(UpdateAggregateTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, name, zone, description, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更新集群"))
        resource = managers.aggregates.get(self.admin_context, resource_id)

        self.update_job_state_desc(job_id, _(u"申请更新集群资源"))

        params = {}
        availability_zone = ''

        def _set_params(key, value):
            if value:
                params.update({key: value})
        _set_params('name', name)
        _set_params('zone', zone)
        _set_params('description', description)

        LOG.info(params)

        rv = get_nova_client().servers.update_aggregate(resource.aggregate_uuid, name, availability_zone=zone)

        self.update_job_state_desc(job_id, _(u"更新集群资源成功"))

        managers.aggregates.update(self.admin_context, resource_id, params)
        self.update_job_state_desc(job_id, _(u"更新集群成功"))

    def revert(self, job_id, *args, **kwargs):
        LOG.error('%s, args: %s, kwargs: %s' % (self.default_provides, args, kwargs))
        LOG.error(kwargs['result'])
        self.update_job_state_desc(job_id, _(u"更新集群失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(UpdateAggregateTask())
    return flow


class AggregateUpdateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None, **kwargs):
        super(AggregateUpdateBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        return managers.aggregates.get(self.context, kwargs['resource_id'])

    def associate_resource_with_job(self, resource, job):
        pass
