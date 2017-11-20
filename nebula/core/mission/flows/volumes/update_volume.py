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

LOG = log.getLogger(__name__)
ACTION = "volume:update"


class UpdateVolumeTask(task.NebulaTask):

    default_provides = 'volume_update'

    def __init__(self):
        super(UpdateVolumeTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, volume_uuid, name, description, **kwargs):
        self.update_job_state_desc(job_id, _(u"申请修改数据卷"))

        volume = get_cinder_client().volumes.update(
            volume_uuid,
            display_name=name,
            display_description=description
        )
        self.update_job_state_desc(job_id, _(u"申请修改数据卷成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"修改数据卷资源失败"))


class PersistentVolumeUpdate(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentVolumeUpdate, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, name, description, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新数据卷存入到数据库"))
        params = dict(
            name=name,
            description=description
        )
        managers.volumes.update(self.admin_context, resource_id, **params)

        self.update_job_state_desc(job_id, _(u"更新数据卷存入到数据库成功"))
        self.update_job_state_desc(job_id, _(u"更新数据卷成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"更新数据卷失败"))


def get_update_data_volume_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        UpdateVolumeTask(),
        PersistentVolumeUpdate()
    )
    return flow


class DataVolumeUpdateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(DataVolumeUpdateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_update_data_volume_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        volume = managers.volumes.get(self.context, kwargs["resource_id"])
        self.store.update(dict(
            name=kwargs["name"],
            description=kwargs["description"],
            volume_uuid=volume.volume_uuid
        ))
        return volume

    def associate_resource_with_job(self, resource, job):
        managers.volumes.update(self.context, resource.id, job_id=job.id)
