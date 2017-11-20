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
from .delete_volume_backup import VolumeBackupDeleteBuilder
from .delete_volume import VolumeDeleteBuilder

QUOTAS = quota.QUOTAS
LOG = log.getLogger(__name__)
ACTION = "volume:recover"


class RecoverDataVolumeTask(task.NebulaTask):

    default_provides = 'volume'

    def __init__(self):
        super(RecoverDataVolumeTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, volume_name, volume_backup_id,
                reservations, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始新建数据卷"))
        resource = managers.volumes.get(self.admin_context, resource_id)
        backup_volume = managers.volume_backups.get(self.admin_context, volume_backup_id)
        self.update_job_state_desc(job_id, _(u"申请新建数据卷"))
        new_volume = get_cinder_client().volumes.create(
            resource.size,
            display_name=volume_name,
            display_description=resource.description,
            snapshot_id=backup_volume.volume_backup_uuid,
            volume_type=resource.cinder_types
        )
        self.update_job_state_desc(job_id, _(u"新建数据卷资源成功"))

        return new_volume._info

    def revert(self, job_id, user_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"新建数据卷资源失败"))
        new_volume = kwargs['result']
        if self.is_current_task_ok(new_volume):
            get_cinder_client().volumes.delete(new_volume['id'])


class PersistentRcoverVolume(task.NebulaTask):

    default_provides = 'persitent_recover_volume'

    def __init__(self):
        super(PersistentRcoverVolume, self).__init__(addons=[ACTION])

    def _wait_volume_create(self, resource_id):
        """等待数据卷回调通知完成(通过消息改变状态后)."""

        def checker():
            volume = managers.volumes.get(self.admin_context, resource_id)

            if volume.status == constants.VOLUME_AVAILABLE:
                return True
            elif volume.status == constants.VOLUME_ERROR:
                raise monitor.ResourceFailureError('Error Volume state')
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait()

    def execute(self, job_id, resource_id, cinder_types, volume, reservations, user_id, new_volume_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"保存新建数据卷申请到数据库"))
        request_context = self.get_request_context(**kwargs)
        managers.volumes.update(request_context, new_volume_id, **{
            'volume_uuid': volume['id']
        })

        self.update_job_state_desc(job_id, _(u"数据卷恢复中"))
        # 等待通知改变状态
        self._wait_volume_create(new_volume_id)

        self.update_job_state_desc(job_id, _(u"新建数据卷成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"新建数据卷存储出错，数据卷资源新建失败"))


class DeleteOriginVolumeInfoTask(task.NebulaTask):

    default_provides = 'delete_volume'

    def __init__(self):
        super(DeleteOriginVolumeInfoTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除源数据卷及备份信息"))
        resource = managers.volumes.get(self.admin_context, resource_id)

        try:
            for vb in resource.volume_backups:
                vb_builder = VolumeBackupDeleteBuilder(
                    self.admin_context,
                    resource_kwargs=dict(
                        resource_id=vb.id
                    )
                )
                vb_builder.build()
        except Exception as err:
            self.update_job_state_desc(job_id, _(u"删除源存储卷备份信息失败"))
            raise err
        try:
            volume_builder = VolumeDeleteBuilder(
                self.admin_context,
                resource_id=resource.id
            )
            volume_builder.build()
        except Exception as err:
            self.update_job_state_desc(job_id, _(u"删除源存储卷备失败"))
            raise err

        self.update_job_state_desc(job_id, _(u"申请删除数据卷成功"))

    def revert(self, job_id,  *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"源数据卷及备份信息删除失败"))
        self.log_current_task_failures(*args, **kwargs)


def get_recover_data_volume_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        RecoverDataVolumeTask(),
        PersistentRcoverVolume(),
        # DeleteOriginVolumeInfoTask()
    )
    return flow


class DataVolumeRecoverBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(DataVolumeRecoverBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_recover_data_volume_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        old_volume = managers.volumes.get(self.context, kwargs["volume_id"])
        reservations = QUOTAS.reserve(
            self.context,
            user_id=old_volume.owner_id,
            **{'volumes': old_volume.size}
        )
        try:
            new_volume = managers.volumes.create(
                old_volume.owner_id,
                name=kwargs["name"],
                size=old_volume.size,
                description=old_volume.description,
                volume_uuid="",
                cinder_types=old_volume.cinder_types
            )
        except Exception as err:
            LOG.info("Create volume faild: %s." % err)
            QUOTAS.rollback(self.context, reservations)
            raise err
        else:
            QUOTAS.commit(self.context, reservations)

        self.store.update(dict(
            new_volume_id=new_volume.id,
            volume_backup_id=kwargs["volume_backup_id"],
            volume_name=kwargs["name"],
            reservations=reservations,
            user_id=old_volume.owner_id,
            cinder_types=old_volume.cinder_types
        ))
        return old_volume

    def associate_resource_with_job(self, resource, job):
        managers.volumes.update(self.context, resource.id, job_id=job.id)
