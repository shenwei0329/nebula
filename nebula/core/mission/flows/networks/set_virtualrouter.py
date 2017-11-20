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
ACTION = 'virtualrouter:set'
convert_bandwidth = lambda x: x*1024


class SetVirtualrouterTask(task.NebulaTask):

    default_provides = 'virtualrouter'

    def __init__(self):
        super(SetVirtualrouterTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, user_id,
                bandwidth_tx, bandwidth_rx, virtualrouter_uuid,
                old_bandwidth_tx, old_bandwidth_rx, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始设置路由器"))
        self.update_job_state_desc(job_id, _(u"申请设置路由器资源"))

        vr = get_neutron_client().update_router(
            virtualrouter_uuid,
            {"router": dict(
                rx=convert_bandwidth(bandwidth_rx),
                tx=convert_bandwidth(bandwidth_tx)
            )}
        )

        self.update_job_state_desc(job_id, _(u"申请更新路由器资源成功"))

        return vr

    def revert(self, job_id, *args, **kwargs):
        LOG.error('%s, args: %s, kwargs: %s' % (self.default_provides, args, kwargs))
        get_neutron_client().update_router(
            kwargs["virtualrouter_uuid"],
            {"router": dict(
                rx=convert_bandwidth(kwargs["old_bandwidth_rx"]),
                tx=convert_bandwidth(kwargs["old_bandwidth_tx"])
            )}
        )

        self.update_job_state_desc(job_id, _(u"设置路由器失败"))


class PersistenSetVirtualrouterTask(task.NebulaTask):

    default_provides = 'set_bandwidth'

    def __init__(self):
        super(PersistenSetVirtualrouterTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, user_id,
                bandwidth_tx, bandwidth_rx, old_bandwidth_tx,
                old_bandwidth_rx, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更虚拟路由器"))

        self.update_job_state_desc(job_id, _(u"设置虚拟路由器带宽成功"))

    def revert(self, job_id, *args, **kwargs):
        request_context = self.get_request_context(**kwargs)
        managers.virtualrouters.update(
            request_context,
            kwargs["resource_id"],
            dict(
                bandwidth_rx=kwargs["old_bandwidth_tx"],
                bandwidth_tx=kwargs["old_bandwidth_rx"]
            )
        )
        self.update_job_state_desc(job_id, _(u"设置路由器失败"))


def get_set_virutalrouter_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        SetVirtualrouterTask(),
        # PersistenSetVirtualrouterTask()
    )
    return flow


class VirtualrouterSetBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None, **kwargs):
        super(VirtualrouterSetBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_set_virutalrouter_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        resource_id = kwargs.pop('resource_id')
        vr = managers.virtualrouters.get(self.context, resource_id)
        rx = kwargs.get("bandwidth_rx", None)
        tx = kwargs.get("bandwidth_tx", None)
        if not rx:
            rx = 0
        if not tx:
            tx = 0

        reservations = QUOTAS.reserve(
            self.context,
            user_id=vr.owner_id,
            **dict(
                bandwidth_rx=rx - vr.bandwidth_rx,
                bandwidth_tx=tx - vr.bandwidth_tx
            )
        )
        try:
            managers.virtualrouters.update(
                self.context,
                resource_id,
                dict(
                    bandwidth_rx=rx,
                    bandwidth_tx=tx
                )
            )
        except Exception as err:
            LOG.info(u"数据库更新虚拟路由器失败: %s." % str(err))
            QUOTAS.rollback(
                self.context,
                reservations,
                user_id=vr.owner_id
            )
            raise err
        else:
            QUOTAS.commit(self.context, reservations, user_id=vr.owner_id)

        self.store.update(
            user_id=vr.owner_id,
            bandwidth_tx=tx,
            bandwidth_rx=rx,
            old_bandwidth_tx=vr.bandwidth_tx,
            old_bandwidth_rx=vr.bandwidth_rx,
            virtualrouter_uuid=vr.virtualrouter_uuid
        )
        return vr

    def associate_resource_with_job(self, resource, job):
        managers.virtualrouters.update(self.context, resource.id, dict(job_id=job.id))
