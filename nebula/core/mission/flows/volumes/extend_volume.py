# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow
from nebula.core import constants

from nebula.core import quota
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    cinder import get_client as get_cinder_client
from nebula.openstack.common import log
from nebula.core.i18n import _
from nebula.core.resource_monitor import monitor

QUOTAS = quota.QUOTAS
LOG = log.getLogger(__name__)
ACTION = "volume:extend"


class ExtendVolumeTask(task.NebulaTask):

    default_provides = 'volume'

    def __init__(self):
        super(ExtendVolumeTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, volume_uuid, size,
                old_size, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始扩容数据卷"))

        self.update_job_state_desc(job_id, _(u"申请扩容数据卷"))
        get_cinder_client().volumes.extend(
            volume_uuid,
            size
        )

        self.update_job_state_desc(job_id, _(u"申请数据卷扩容成功"))

    def revert(self, job_id, user_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        result = kwargs['result']
        if self.is_current_task_ok(result):
            get_cinder_client().volumes.extend(
                kwargs["volume_uuid"],
                kwargs["old_size"]
            )
        self.update_job_state_desc(job_id, _(u"申请扩容数据卷失败"))


class PersistentExtendDataVolume(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentExtendDataVolume, self).__init__(addons=[ACTION])

    def _wait_extend_volume(self, resource_id):
        """等待数据卷完成(通过消息改变状态后)."""

        def checker():
            volume = managers.volumes.get(self.admin_context, resource_id)
            LOG.info("The volume current state:%s" % volume.status)
            if volume.status in [constants.VOLUME_AVAILABLE,
                                 constants.VOLUME_IN_USE]:
                return True
            elif volume.status == constants.VOLUME_ERROR:
                raise monitor.ResourceFailureError('Error Volume state')
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait()

    def execute(self, job_id, resource_id, volume_uuid,
                size, old_size, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入扩容数据卷到数据库，等待消息通知"))

        self.update_job_state_desc(job_id, _(u"数据卷扩容中"))
        # 等待通知改变状态
        self._wait_extend_volume(resource_id)

        self.update_job_state_desc(job_id, _(u"存入扩容数据卷到数据库成功"))
        self.update_job_state_desc(job_id, _(u"扩容数据卷成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        request_context = self.get_request_context(**kwargs)

        # managers.volumes.update(
        #     request_context,
        #     kwargs["resource_id"],
        #     size=kwargs["old_size"],
        #     status=constants.VOLUME_ERROR
        # )
        self.update_job_state_desc(job_id, _(u"创建数据卷失败"))


def get_extend_volume_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        ExtendVolumeTask(),
        PersistentExtendDataVolume()
    )
    return flow


class DataVolumeExtendBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(DataVolumeExtendBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_extend_volume_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        volume = managers.volumes.get(self.context, kwargs["resource_id"])

        reservations = QUOTAS.reserve(self.context,
                                      user_id=volume.owner_id,
                                      **{'volumes': kwargs["resize"] - volume.size}
        )
        try:
            managers.volumes.update(
                self.context,
                kwargs["resource_id"],
                size=kwargs["resize"],
                status=constants.VOLUME_EXTENDING
            )
        except Exception as err:
            LOG.info("Extend volume faild: %s." % err)
            QUOTAS.rollback(self.context, reservations)
            raise err
        else:
            QUOTAS.commit(self.context, reservations)

        self.store.update(
            volume_uuid=volume.volume_uuid,
            size=kwargs["resize"],
            old_size=volume.size,
            user_id=volume.owner_id
        )
        return volume

    def associate_resource_with_job(self, resource, job):
        managers.volumes.update(self.context, resource.id, job_id=job.id)
