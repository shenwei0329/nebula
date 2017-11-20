# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow
import re

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
ACTION = 'virtualrouter:delete'


class DeleteVirtualrouterTask(task.NebulaTask):

    default_provides = 'callapi'

    def __init__(self):
        super(DeleteVirtualrouterTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除虚拟路由器"))
        resource = managers.virtualrouters.get(self.admin_context, resource_id)

        self.update_job_state_desc(job_id, _(u"开始删除虚拟路由器资源"))
        try:
            get_neutron_client().delete_router(
                resource.virtualrouter_uuid
            )
        except Exception as err:
            error = str(err)
            if re.search(r'[\w|-]{36}|None\sdoes not exist', error):
                #self.update_job_state_desc(job_id, _(u"虚拟路由器已经被删除，可以忽略！"))
                pass
            elif re.search(r'[\w|-]{36}|could not be found', error):
                pass
            else:
                self.update_job_state_desc(job_id, _(error))
                raise err
        self.update_job_state_desc(job_id, _(u"删除虚拟路由器资源成功"))
        self.update_job_state_desc(job_id, _(u"开始删除数据库记录"))

        reservations = QUOTAS.reserve(
            self.get_request_context(**kwargs),
            user_id=resource.owner_id,
            **{'virtual_routers': -1,
               'bandwidth_tx': -resource.bandwidth_tx,
               'bandwidth_rx': -resource.bandwidth_rx
            }
        )
        try:
            managers.virtualrouters.delete(resource_id)
        except Exception as err:
            self.update_job_state_desc(job_id, _(u"数据库删除虚拟路由器失败"))
            QUOTAS.rollback(
                self.get_request_context(**kwargs),
                reservations,
                user_id=user_id
            )
            raise err
        else:
            QUOTAS.commit(self.get_request_context(**kwargs), reservations, user_id=user_id)

        self.update_job_state_desc(job_id, _(u"删除虚拟路由器成功"))

    def revert(self, job_id, user_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"删除虚拟路由器失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeleteVirtualrouterTask())
    return flow


class VirtualrouterDeleteBuilder(Builder):

    def __init__(self, context=None, resource_kwargs=None, **kwargs):
        super(VirtualrouterDeleteBuilder, self).__init__(
            context=context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        vr = managers.virtualrouters.get(self.context, kwargs['resource_id'])
        self.store.update(
            user_id=vr.owner_id,
        )
        return vr

    def associate_resource_with_job(self, resource, job):
        managers.virtualrouters.update(self.context, resource.id, dict(job_id=job.id))
