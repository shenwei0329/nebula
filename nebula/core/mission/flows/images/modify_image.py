# -*- coding: utf-8 -*-

import logging
from taskflow import retry
from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import flow_builder
from nebula.core.mission import task
from nebula.core.openstack_clients import glance
from nebula.core.i18n import _

ACTION = 'image:modify'

LOG = logging.getLogger(__name__)


class ModifyOSImageTask(task.NebulaTask):
    def __init__(self):
        super(ModifyOSImageTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, image_uuid, image_name,
                image_description, **kwargs):

        self.update_job_state_desc(job_id, _(u"开始更新镜像"))
        glance.get_client().images.update(image_uuid, name=image_name)

    def revert(self,job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"更新镜像失败"))


class ModifyImageEntityTask(task.NebulaTask):
    def __init__(self):
        super(ModifyImageEntityTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, image_uuid, image_name,
                image_description, **kwargs):

        managers.images.update(self.admin_context,
                               resource_id=resource_id,
                               name=image_name,
                               description=image_description)
        self.update_job_state_desc(job_id, _(u"更新镜像成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, u'更新镜像失败')


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(ModifyOSImageTask(), ModifyImageEntityTask())
    return flow


class ImageUpdateBuilder(flow_builder.Builder):
    def __init__(self, context, resource_kwargs=None, store=None):
        super(ImageUpdateBuilder, self).__init__(
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
        self.store.update({'image_uuid': image.image_uuid,
                           'image_name': kwargs['name'],
                           'image_description': kwargs['description']})
        return image
