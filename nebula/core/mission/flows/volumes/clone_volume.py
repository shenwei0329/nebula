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
ACTION = "volume:clone"


class CloneVolumeTask(task.NebulaTask):

    default_provides = 'volume'

    def __init__(self):
        super(CloneVolumeTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, source_volid, name,
                size, description, volume_types, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始克隆数据卷"))
        self.update_job_state_desc(job_id, _(u"申请克隆数据卷"))
        LOG.info("Clone volume good1")
        clone_volume = get_cinder_client().volumes.create(size,
                                                          source_volid=source_volid,
                                                          display_name=name,
                                                          display_description=description,
                                                          volume_type=volume_types)

        self.update_job_state_desc(job_id, _(u"申请数据卷克隆成功"))
        return clone_volume._info

    def revert(self, user_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        clone_volume = kwargs['result']
        if self.is_current_task_ok(clone_volume):
            get_cinder_client().volumes.delete(clone_volume['id'])


class PersistentCloneDataVolume(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentCloneDataVolume, self).__init__(addons=[ACTION])

    def _wait_volume_create(self, resource_id):
        """等待数据卷克隆(创建)完成(通过消息改变状态后)."""

        def checker():
            volume = managers.volumes.get(self.admin_context, resource_id)
            LOG.info("The volume current state:%s" % volume.status)
            if volume.status == constants.VOLUME_AVAILABLE:
                return True
            elif volume.status == constants.VOLUME_ERROR:
                raise monitor.ResourceFailureError('Error Volume state')
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait()

    def execute(self, job_id, resource_id, volume, clone_resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入克隆数据卷到数据库"))

        LOG.info("clone volume openstack result: %s" % volume)
        self.update_job_state_desc(job_id, _(u"数据卷克隆中"))
        clone_resource = managers.volumes.update(
            self.get_request_context(**kwargs),
            clone_resource_id,
            volume_uuid=volume["id"]
        )
        # 等待通知改变状态
        self._wait_volume_create(clone_resource.id)

        self.update_job_state_desc(job_id, _(u"存入克隆数据卷到数据库成功"))
        self.update_job_state_desc(job_id, _(u"克隆数据卷成功"))
        return clone_resource

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"克隆数据卷失败"))


def get_clone_data_volume_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CloneVolumeTask(),
             PersistentCloneDataVolume())
    return flow


class DataVolumeCloneBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(DataVolumeCloneBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_clone_data_volume_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        source_volume = managers.volumes.get(self.context, kwargs["resource_id"])

        reservations = QUOTAS.reserve(self.context,
                                      user_id=source_volume.owner_id,
                                      **{'volumes': source_volume.size}
        )
        try:
            LOG.info("Clone volume good")
            LOG.info(source_volume.cinder_types)
            clone_resource = managers.volumes.create(
                source_volume.owner_id,
                name=kwargs["name"],
                size=source_volume.size,
                cinder_types=source_volume.cinder_types,
                description=source_volume.description
            )
        except Exception as err:
            LOG.info("Clone volume faild: %s." % err)
            QUOTAS.rollback(self.context, reservations)
            raise err
        else:
            QUOTAS.commit(self.context, reservations)

        self.store.update(dict(
            source_volid=source_volume.volume_uuid,
            clone_resource_id=clone_resource.id,
            name=kwargs["name"],
            size=source_volume.size,
            volume_types=source_volume.cinder_types,
            description=source_volume.description,
            user_id=source_volume.owner_id
        ))
        return source_volume

    def associate_resource_with_job(self, resource, job):
        managers.volumes.update(self.context, resource.id, job_id=job.id)
