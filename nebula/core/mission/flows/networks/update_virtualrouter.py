# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    neutron import get_client as get_neutron_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = 'virtualrouter:update'


class UpdateVirtualrouterTask(task.NebulaTask):

    default_provides = 'callapi'

    def __init__(self):
        super(UpdateVirtualrouterTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, name, description, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更新路由器"))
        resource = managers.virtualrouters.get(self.admin_context, resource_id)

        self.update_job_state_desc(job_id, _(u"申请更新路由器资源"))

        params = {}
        def _set_params(key, value):
            if value:
                params.update({key: value})
        _set_params('name', name)

        rv = get_neutron_client().update_router(
            resource.virtualrouter_uuid,
            body={'router': params}
        )
        self.update_job_state_desc(job_id, _(u"更新路由器资源成功"))

        _set_params('description', description)
        managers.virtualrouters.update(self.admin_context, resource_id, params)
        self.update_job_state_desc(job_id, _(u"更新路由器成功"))

    def revert(self, job_id, *args, **kwargs):
        LOG.error('%s, args: %s, kwargs: %s' % (self.default_provides, args, kwargs))
        LOG.error(kwargs['result'])
        self.update_job_state_desc(job_id, _(u"更新路由器失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(UpdateVirtualrouterTask())
    return flow


class VirtualrouterUpdateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None, **kwargs):
        super(VirtualrouterUpdateBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        return managers.virtualrouters.get(self.context, kwargs['resource_id'])

    def associate_resource_with_job(self, resource, job):
        managers.virtualrouters.update(self.context,
                                       resource.id, dict(job_id=job.id))
