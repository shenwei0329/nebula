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
ACTION = 'host:update'


class HostUpdateTask(task.NebulaTask):
    default_provides = 'host'

    def __init__(self):
        super(HostUpdateTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, hostname, os_user,
                os_user_pwd, **kwargs):

        self.update_job_state_desc(job_id, _(u"资源更新中"))

        params = dict(
            hostname=hostname,
            os_user=os_user,
            os_user_pwd=os_user_pwd,
        )

        LOG.info("update-params=%s", params)

        managers.compute_nodes.update(self.admin_context,
                                      resource_id,
                                      params)

        self.update_job_state_desc(job_id, _(u"修改主机成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"修改主机失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(HostUpdateTask())
    return flow


class HostUpdateBuilder(Builder):

    def __init__(self, context, resource_args=(),
                 resource_kwargs=None, **kwargs):

        super(HostUpdateBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        return managers.compute_nodes.get(self.context, kwargs['resource_id'])


    def associate_resource_with_job(self, resource, job):
        managers.compute_nodes.update(self.context,
                                      resource.id,
                                      dict(job_id=job.id))
