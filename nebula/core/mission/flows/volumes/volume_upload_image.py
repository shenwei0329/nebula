# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow
from nebula.core import constants

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    cinder import get_client as get_cinder_client
from nebula.openstack.common import log
from nebula.core.i18n import _
from nebula.core.resource_monitor import monitor
from nebula.core.openstack_clients import glance
from nebula.core.quota import QUOTAS

LOG = log.getLogger(__name__)
ACTION = "volume_upload_image:create"


class UploadVolumeImageTask(task.NebulaTask):

    default_provides = 'volume_upload_image'

    def __init__(self):
        super(UploadVolumeImageTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, image_id, name, volume_uuid, os_type, disk_format, container_format,user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始数据卷转换镜像"))
        self.update_job_state_desc(job_id, _(u"开始申请数据卷转换镜像"))
        
        #默认情况下，container_format='bare'和disk_format='qcow2'
        image_info = get_cinder_client().volumes.upload_to_image(
            volume=volume_uuid,
            disk_format=disk_format,
            image_name=name,
            container_format=container_format,
            force='False'
        )
        self.update_job_state_desc(job_id, _(u"申请数据卷转换镜像成功"))
        LOG.info("image info: %s" % image_info[1])

        min_size = image_info[1].get("os-volume_upload_image").get('size')
        name = image_info[1].get("os-volume_upload_image").get('image_name')
        description = image_info[1].get("os-volume_upload_image").get('display_description')
        image_uuid = image_info[1].get("os-volume_upload_image").get('image_id')
        values = dict(
            image_uuid=image_uuid,
            status='queued',
            is_public=True,
            size=min_size,
            min_disk=min_size,
            name=name,
            description=description,
            owner_id=user_id
        )
        managers.images.update_by_id(
            self.admin_context,
            image_id,
            values
        )
        
        #os_type = {'os_type': os_type}
        #LOG.info("UploadVolumeImageTask_1::::::")
        #LOG.info(image_uuid)
        #LOG.info(min_size)
        #glance.get_client().images.update(
        #   image=image_uuid,
        #    min_disk=min_size,
        #    is_public='True',
         #   properties=os_type
        #)
        return image_info[1].get("os-volume_upload_image")

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        LOG.info(kwargs)
        volume_upload_image = kwargs['result']
        if self.is_current_task_failed(volume_upload_image):
            if volume_upload_image.get('image_id'):
                glance.get_client().images.delete(volume_upload_image['image_id'])
        self.update_job_state_desc(job_id, _(u"申请数据卷转换镜像失败"))


class PersistentVolumeUploadImage(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentVolumeUploadImage, self).__init__(addons=[ACTION])

    def _wait_volume_image_upload(self, job_id, image_uuid, owner_id):
        """等待数据卷转换镜像完成(通过消息改变状态后)."""
        def checker():
            values = dict(
                image_uuid=image_uuid
            )
            volume_image = managers.\
                images.get_by(self.admin_context, **values)
            if volume_image.status == 'active':
                return True
            elif volume_image.status == 'error':
                raise res_mon.ResourceFailureError('Error Volume UploadImage state')
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait(timeout=3600)
        self.update_job_state_desc(job_id, _(u"数据卷转换镜像成功"))

    def execute(self, job_id, os_type, user_id, volume_upload_image, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入数据卷镜像到数据库"))

        self.update_job_state_desc(job_id, _(u"数据卷创建镜像中"))
        # 等待通知改变状态
        image_uuid = volume_upload_image.get('image_id')
        self._wait_volume_image_upload(job_id, image_uuid, user_id)
        
        #将镜像置成is-public=true
        LOG.info("UploadVolumeImageTask_2::::::")
        LOG.info(image_uuid)
        os_type = {'os_type': os_type}
        glance.get_client().images.update(
            image=image_uuid,
            min_disk=volume_upload_image['size'],
            is_public='True',
            properties=os_type
        )
        
        self.update_job_state_desc(job_id, _(u"存入数据卷镜像到数据库成功"))
        self.update_job_state_desc(job_id, _(u"数据卷转换镜像成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)     
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, _(u"数据卷转换镜像失败"))


def get_upload_volume_image_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        UploadVolumeImageTask(),
        PersistentVolumeUploadImage()
    )
    return flow


class VolumeUploadImageBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(VolumeUploadImageBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_upload_volume_image_flow,
            )

    def prepare_resource(self, *args, **kwargs):
        volume_id = kwargs["resource_id"]
        volume = managers.volumes.get(self.context, volume_id)
        #预分配资源
        values = dict(images=1)
        reservations = QUOTAS.reserve(self.context,
                                      user_id=volume.owner_id,
                                      **values)
        if volume.cinder_types=='vmware':
            disk_format='vmdk'
            container_format='bare'
        else :
            disk_format="qcow2"
            container_format="bare"
        try:
            image = managers.images.create(
                volume.owner_id,
                name=kwargs["name"],
                disk_format=disk_format,
                container_format=container_format,
                size=volume.size,
                min_disk=volume.size,
                os_type=kwargs["os_type"],
                architecture=""
            )
        except Exception as err:
            LOG.info("Volume upload image faild: %s." % str(err))
            QUOTAS.rollback(self.context, reservations, volume.owner_id)
            raise err
        else:
            QUOTAS.commit(self.context, reservations, volume.owner_id)
        params = dict(
            volume_uuid=volume.volume_uuid,
            image_id=image.id,
            name=kwargs["name"],
            user_id=volume.owner_id,
            os_type=kwargs["os_type"],
            disk_format=disk_format,
            container_format=container_format
        )
        self.store.update(params)
        return volume

    def associate_resource_with_job(self, resource, job):
        managers.volumes.update(self.context, resource.id, job_id=job.id)
