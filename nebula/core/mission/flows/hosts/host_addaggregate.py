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
ACTION = 'host:add_aggregate'


class AddAggregateTask(task.NebulaTask):
    default_provides = 'host'

    def __init__(self):
        super(AddAggregateTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, hostname, aggregate_id, **kwargs):
        """

        :param job_id:
        :param hostname:      主机OS_HOST_NAME
        :param aggregate_id:  集群ID
        :param kwargs:
        :return:
        """
        self.update_job_state_desc(job_id, _(u"验证主机资源"))

        #得到集群数据
        aggregate = managers.aggregates.get(self.admin_context, aggregate_id)

        self.update_job_state_desc(job_id, _(u"资源申请中"))
        rv = get_nova_client().servers.\
            add_host_aggregate(aggregate.aggregate_uuid, hostname)
        return rv

    def revert(self, job_id,*args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        rv = kwargs['result']
        #回滚
        if self.is_current_task_ok(rv):
            get_nova_client().servers.\
                remove_host_aggregate(rv["id"], kwargs['hostname'])
        else:
            self.update_job_state_desc(job_id, _(u"加入集群失败"))


class AddAggregateUpdateTask(task.NebulaTask):
    def __init__(self):
        super(AddAggregateUpdateTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, aggregate_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新数据库记录"))
        managers.compute_nodes.update(self.admin_context,
                                      resource_id,
                                      {'aggregate_id': aggregate_id})
        # 绑定集群ID
        self.update_job_state_desc(job_id, _(u"加入集群成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"加入集群失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(AddAggregateTask(),
             AddAggregateUpdateTask())
    return flow


class AddAggregateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None,
                 **kwargs):
        super(AddAggregateBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        host = managers.compute_nodes.get(self.context, kwargs['resource_id'])
        self.store.update(dict(hostname=host.os_hostname,
                               aggregate_id=kwargs['aggregate_id']
        ))
        return host

    def associate_resource_with_job(self, resource, job):
        managers.compute_nodes.update(self.context,
                                      resource.id,
                                      dict(job_id=job.id))
