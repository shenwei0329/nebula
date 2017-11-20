# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients.nova import get_client as get_nova_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = 'aggregate:create'


class CreateAggregateTask(task.NebulaTask):

    default_provides = 'aggregate'

    def __init__(self):
        super(CreateAggregateTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建集群"))
        resource = managers.aggregates.get(self.admin_context, resource_id)

        self.update_job_state_desc(job_id, _(u"申请集群资源"))
        rv = get_nova_client().servers.create_aggregate(
            name=resource.name,
            availability_zone=resource.zone, # 指定az名称与aggregate同名
        )
        self.update_job_state_desc(job_id, _(u"集群资源申请成功"))

        return rv['aggregate']

    def revert(self, job_id, *args, **kwargs):
        LOG.error('%s, args: %s, kwargs: %s' % (self.default_provides, args, kwargs))
        LOG.error(kwargs['result'])
        self.update_job_state_desc(job_id, _(u"集群资源申请失败"))

        aggregate = kwargs['result']
        if self.is_current_task_failed(aggregate) and "id" in aggregate:
            get_nova_client().servers.delete_aggregate(aggregate['id'])


class PersistentAggregate(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentAggregate, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, aggregate, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入数据库"))

        managers.aggregates.update(self.admin_context,
                                   resource_id,
                                   {'aggregate_uuid': aggregate['id']})
        self.update_job_state_desc(job_id, _(u"存入数据库成功"))
        self.update_job_state_desc(job_id, _(u"创建集群成功"))

    def revert(self, job_id, *args, **kwargs):
        LOG.error('%s, args: %s, kwargs: %s' % (self.default_provides, args, kwargs))
        LOG.error(kwargs['result'])
        self.update_job_state_desc(job_id, _(u"创建集群失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreateAggregateTask(), PersistentAggregate())
    return flow


class AggregateCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None, **kwargs):
        super(AggregateCreateBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        LOG.info(kwargs)
        return managers.aggregates.create(self.context.user_id, **kwargs)

    def associate_resource_with_job(self, resource, job):
        pass
