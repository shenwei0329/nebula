# -*- coding: utf-8 -*-
import logging

from taskflow import retry
from taskflow.patterns import linear_flow

from nebula.core import constants
from nebula.core.managers import managers
from nebula.core.mission import flow_builder
from nebula.core.mission import task
from nebula.core.openstack_clients import glance
from nebula.core.resource_monitor import monitor as res_mon
from nebula.core.i18n import _
from glanceclient import exc as glance_exc

ACTION = 'image:delete'

LOG = logging.getLogger(__name__)


class DeleteOSImageTask(task.NebulaTask):
    def __init__(self):
        super(DeleteOSImageTask, self).__init__(addons=[ACTION])

    def _wait_instance_deletion(self, resource_id):
        
        LOG.info("DeleteOSImageTask_update_22")  
        update_values=dict(resource_id=resource_id,status='deleted')
        managers.images.update(self.admin_context, **update_values)
        
        def checker():
            image_ref = managers.images.get(self.admin_context, resource_id)
            if not image_ref:
                # 严重错误, 没有找到相应实体
                raise res_mon.ResourceFailureError('Entity not found')
            elif image_ref.status in (constants.IMAGE_STATUS_KILLED,
                                         constants.IMAGE_STATUS_DELETED):
                # 状态为 active, 删除完成
                return True
            return False

        monitor = res_mon.ResourceChangeMonitor(checker)
        # 等待完成或错误(包括超时)
        monitor.wait()       

    def execute(self, job_id, resource_id, image_uuid, **kwargs):
        LOG.info("DeleteOSImageTask_1:::::")
        LOG.info(resource_id)
        LOG.info(image_uuid)
        self.update_job_state_desc(job_id, _(u"开始删除镜像"))
        try:
            glance.get_client().images.delete(image_uuid)
            self._wait_instance_deletion(resource_id)     
        except glance_exc.HTTPNotFound:
            # Image is deleted, no need to delete it again
            LOG.info("DeleteOSImageTask_2.4")
            update_values=dict(resource_id=resource_id,status=constants.IMAGE_STATUS_DELETED)
            managers.images.update(self.admin_context, **update_values)
            raise Exception('this image is not exist')

    def revert(self, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)


class DeleteImageEntityTask(task.NebulaTask):
    def __init__(self):
        super(DeleteImageEntityTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, image_uuid, **kwargs):
        #managers.images.delete(self.admin_context, resource_id)
        self.update_job_state_desc(job_id, _(u"删除镜像成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, u'删除镜像失败')


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeleteOSImageTask(), DeleteImageEntityTask())
    return flow


class ImageDeleteBuilder(flow_builder.Builder):
    def __init__(self, context, resource_kwargs=None, store=None):
        super(ImageDeleteBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            store=store)

    def associate_resource_with_job(self, resource, job):
        managers.images.update_by_id(self.context,
                                     resource.id,
                                     dict(job_id=job.id))

    def prepare_resource(self, *args, **kwargs):
        image = managers.images.get(self.context, kwargs['resource_id'])
        self.store.update({'image_uuid': image.image_uuid})
        return image
