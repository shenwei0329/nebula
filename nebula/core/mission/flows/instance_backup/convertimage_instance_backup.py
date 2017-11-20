# -*- coding: utf-8 -*-

from taskflow import retry
from taskflow.patterns import linear_flow
import logging
from nebula.core.managers import managers
from nebula.core.mission import flow_builder
from nebula.core.mission import task
from nebula.core.resource_monitor import monitor
from nebula.core.openstack_clients import nova
from nebula.core.openstack_clients import glance
from nebula.core.i18n import _

from novaclient import exceptions as nova_exc

from nebula.core.quota import QUOTAS

LOG = logging.getLogger(__name__)

ACTION = 'instanceBackup:convert_image'


class ConvertImageInstanceBackUpFind(task.NebulaTask):
    def __init__(self):
        super(ConvertImageInstanceBackUpFind, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, instance_uuid, backup_uuid, owner_id, reservations, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始查询指定虚机备份"))
        nova.get_client().servers.get_backup_v2(instance_uuid, backup_uuid)
        self.update_job_state_desc(job_id, _(u"查询指定虚机备份成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        QUOTAS.rollback(
            self.get_request_context(**kwargs),
            kwargs['reservations'],
            user_id=kwargs['owner_id']
        )
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, _(u'查询指定虚机备份失败'))

        # 只是查询instance_backup是否存在，因此不需要考虑回滚


class ConvertImageInstanceBackUpExist(task.NebulaTask):

    default_provides = 'image_info'

    def __init__(self):
        super(ConvertImageInstanceBackUpExist, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, backup_uuid, instance_uuid,
                owner_id, image_name, Description, base_image_ref, **kwargs):
        LOG.info("ConvertImageInstanceBackUpExist_1:::::")
        LOG.info(owner_id)
        self.update_job_state_desc(job_id, _(u"开始验证虚机备份转换镜像"))
        values = dict(
            base_image_ref=backup_uuid,
            status='queued',
            is_public=True,
            size=0,
            min_disk=0,
            min_ram=0,
            name=image_name,
            description=Description,
            owner_id=owner_id
        )
        return values

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, u'验证虚机备份失败')

class ConvertImageInstanceBackup(task.NebulaTask):
    def __init__(self):
        super(ConvertImageInstanceBackup, self).__init__(addons=[ACTION])

    def _wait_convertimage_instancebackup(self, job_id, resource_id, image_name,
                                          owner_id,
                                          image_uuid, reservations,
                                          backup_uuid, **kwargs):
        """等待虚机备份转换成镜像，并上传至glance服务(通过消息改变状态)."""

        def checker():
            values = dict(
                image_uuid=image_uuid
            )
            backup_image = managers.\
                images.get_by(self.admin_context, **values)
            if backup_image.status == 'active':
                #更新该虚机备份状态：converting->active
                update_values = dict(status='active')
                managers.instance_backups.\
                    update_by_backup_uuid(self.admin_context,
                                          backup_uuid,
                                          update_values)
                return True
            elif backup_image.status == 'error':
                raise res_mon.ResourceFailureError('Error InstanceBackup ConvertImage state')
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait(timeout=10600)
        QUOTAS.commit(self.admin_context, reservations, owner_id)
        self.update_job_state_desc(job_id, _(u"上传镜像成功"))

    def execute(self, job_id, image_info, resource_id, backup_uuid,
                instance_uuid, image_name, owner_id, reservations,
                **kwargs):
        #更新该虚机备份状态：active->converting
        values = dict(status='converting')
        managers.instance_backups.update_by_backup_uuid(self.admin_context,
                                                        backup_uuid,
                                                        values)

        self.update_job_state_desc(job_id, _(u"后台虚机备份转换成镜像开始"))
        try:
            image_uuid = nova.get_client().servers.\
                convertimage_backup_v2(instance_uuid,
                                       backup_uuid,
                                       image_name)

            LOG.info("ConvertImageInstanceBackup_1234:::::")
            if image_uuid is None:
                self.update_job_state_desc(job_id, u'后台虚机备份error')
                raise Exception("后台虚机备份error")
        
            delete_image_values = dict(image_uuid=image_uuid)
            images_sync_info=managers.images.get_by(self.admin_context, **delete_image_values)
            LOG.info("ConvertImageInstanceBackup_2::::::::::")
            if images_sync_info:
                LOG.info("ConvertImageInstanceBackup_3::::::::::")
                LOG.info(images_sync_info.image_uuid)
                managers.images.delete_by(self.admin_context, delete_image_values)
                
            managers.images.create_by_image_uuid(self.admin_context,
                                                 image_uuid,
                                                 **image_info)
            self.update_job_state_desc(job_id, _(u"虚机备份转换成镜像成功,并开始上传镜像"))

            self._wait_convertimage_instancebackup(
                job_id,
                resource_id,
                image_name,
                owner_id,
                image_uuid,
                reservations,
                backup_uuid
                )
        except Exception as ex:
            if image_uuid is not None:
                #删除底层glance数据库数据
                glance.get_client().images.delete(image_uuid)
                #删除nebula数据库数据
                delete_image_values = dict(image_uuid=image_uuid)
                managers.images.delete_by(self.admin_context, delete_image_values)
            self.update_job_state_desc(job_id, _(u"底层出错"))
            raise ex
        return image_uuid

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        #更新该虚机备份状态：converting->active
        values = dict(status='active')
        managers.instance_backups.update_by_backup_uuid(self.admin_context,
                                                        kwargs['backup_uuid'],
                                                        values)
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, u'后台虚机备份转换成镜像失败')


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(ConvertImageInstanceBackUpFind(),
             ConvertImageInstanceBackUpExist(),
             ConvertImageInstanceBackup())
    return flow


class InstanceBackUpConvertImageBuilder(flow_builder.Builder):
    def __init__(self, context, resource_kwargs=None, store=None):
        super(InstanceBackUpConvertImageBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            store=store)

    def associate_resource_with_job(self, resource, job):
        managers.instance_backups.update_by_id(self.context,
                                               resource.id,
                                               dict(job_id=job.id))

    def prepare_resource(self, *args, **kwargs):
        record = managers.instance_backups.get(self.context,
                                               kwargs['resource_id'])

        store_data = dict(
            backup_uuid=record.backup_uuid,
            base_image_ref=record.backup_uuid,
            image_name=kwargs['name'],
            Description=kwargs['Description'],
            owner_id=record.owner_id,
            instance_uuid='123456789',  # 该接口已修改，该参数已失效
        )
        values = dict(images=1)
        reservations = QUOTAS.reserve(self.context,
                                      user_id=record.owner_id,
                                      **values)
        store_data.update(dict(reservations=reservations))
        self.store.update(store_data)
        LOG.info(self.store)
        return record
