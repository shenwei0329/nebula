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
ACTION = 'host:maintain'


class SetMaintainTask(task.NebulaTask):
    default_provides = 'host'

    def __init__(self):
        super(SetMaintainTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, hostname, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新主机状态中"))
        get_nova_client().servers.check_disable_compute_node(hostname)

    def revert(self, job_id, hostname, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        rv = kwargs['result']
        #回滚
        if self.is_current_task_ok(rv):
            get_nova_client().servers.check_enable_compute_node(hostname)
        else:
            self.update_job_state_desc(job_id, _(u"主机置维护失败"))


class UpdateTask(task.NebulaTask):
    def __init__(self):
        super(UpdateTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, hostname, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新数据库记录"))

        managers.compute_nodes.\
            update(self.admin_context,
                   resource_id,
                   {'status': constants.HOST_STATUS_MAINTAIN})

        self.update_job_state_desc(job_id, _(u"主机置维护成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"主机置维护失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        SetMaintainTask(),
        UpdateTask())
    return flow


class SetMaintainBuilder(Builder):

    def __init__(self, context, resource_args=(),
                 resource_kwargs=None, **kwargs):

        super(SetMaintainBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        host = managers.compute_nodes.get(self.context, kwargs['resource_id'])
        self.store.update(dict(hostname=host.os_hostname))
        return host

    def associate_resource_with_job(self, resource, job):
        managers.compute_nodes.update(self.context,
                                      resource.id,
                                      dict(job_id=job.id))
