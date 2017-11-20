# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core import quota
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    neutron import get_client as get_neutron_client
from nebula.openstack.common import log
from nebula.core.i18n import _

QUOTAS = quota.QUOTAS
LOG = log.getLogger(__name__)
ACTION = 'virtualrouter:create'


class CreateVirtualrouterTask(task.NebulaTask):

    default_provides = 'virtualrouter'

    def __init__(self):
        super(CreateVirtualrouterTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建路由器"))
        resource = managers.virtualrouters.get(self.admin_context, resource_id)

        convert_bandwidth = lambda x: x*1024
        self.update_job_state_desc(job_id, _(u"申请虚拟路由器资源"))

        rv = get_neutron_client().create_router(
            body={'router':
                      {"name": resource.name,
                       'admin_state_up': "true",
                       #
                       # 2015.7.8 by shenwei.
                       #
                       #'rx': convert_bandwidth(resource.bandwidth_rx),
                       #'tx': convert_bandwidth(resource.bandwidth_tx)
                       #
                      }
            }
        )
        self.update_job_state_desc(job_id, _(u"申请虚拟路由器资源成功"))
        return rv['router']

    def revert(self, *args, **kwargs):
        LOG.error('%s, args: %s, kwargs: %s' % (self.default_provides, args, kwargs))
        LOG.error(kwargs['result'])

        virtualrouter = kwargs['result']
        if self.is_current_task_failed(virtualrouter):
            get_neutron_client().delete_router(virtualrouter['id'])


class PersistentVirtualrouter(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentVirtualrouter, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, virtualrouter, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入数据库"))

        managers.virtualrouters.update(
            self.admin_context,
            resource_id,
            {'virtualrouter_uuid': virtualrouter['id']}
        )

        self.update_job_state_desc(job_id, _(u"存入数据库成功"))
        self.update_job_state_desc(job_id, _(u"创建虚拟路由器成功"))

    def revert(self, job_id, *args, **kwargs):
        LOG.error('%s, args: %s, kwargs: %s' % (self.default_provides, args, kwargs))
        LOG.error(kwargs['result'])
        self.update_job_state_desc(job_id, _(u"创建虚拟路由器失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreateVirtualrouterTask(), PersistentVirtualrouter())
    return flow


class VirtualrouterCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None, **kwargs):
        super(VirtualrouterCreateBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):

        rx = kwargs.get("bandwidth_rx", None) if kwargs.get("bandwidth_rx", None) else 1
        tx = kwargs.get("bandwidth_tx", None) if kwargs.get("bandwidth_tx", None) else 1
        reservations = QUOTAS.reserve(self.context,
                                      **{'virtual_routers': 1,
                                         'bandwidth_tx': tx,
                                         'bandwidth_rx': rx
                                         }
        )
        try:
            vr = managers.virtualrouters.create(self.context.user_id, **kwargs)
        except Exception as err:
            LOG.info("Create virtualrouter faild: %s." % err)
            QUOTAS.rollback(self.context, reservations)
            raise err
        else:
            QUOTAS.commit(self.context, reservations)

        return vr

    def associate_resource_with_job(self, resource, job):
        managers.virtualrouters.update(self.context, resource.id, dict(job_id=job.id))
