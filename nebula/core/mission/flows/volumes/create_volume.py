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
ACTION = "volume:create"


class CreateVolumeTask(task.NebulaTask):

    default_provides = 'volume'

    def __init__(self):
        super(CreateVolumeTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建数据卷"))
        resource = managers.volumes.get(self.admin_context, resource_id)
        
        print("CreateVolumeTask_1::::")
        print(resource)
        self.update_job_state_desc(job_id, _(u"申请创建数据卷"))
        volume = get_cinder_client().volumes.create(resource.size,
                                                    display_name=resource.name,
                                                    display_description=resource.description,
                                                    volume_type=resource.cinder_types)
        self.update_job_state_desc(job_id, _(u"申请数据卷资源成功"))
        return volume._info

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)

        # roll back volume quota
        LOG.info(u"数据卷配额回滚")

        self.update_job_state_desc(job_id, _(u"创建数据卷失败"))
        volume = kwargs['result']
        if self.is_current_task_ok(volume):
            get_cinder_client().volumes.delete(volume['id'])



class PersistentDataVolume(task.NebulaTask):

    default_provides = 'persitent'

    def __init__(self):
        super(PersistentDataVolume, self).__init__(addons=[ACTION])

    def _wait_volume_create(self, resource_id):
        """等待数据卷完成(通过消息改变状态后)."""

        def checker():
            volume = managers.volumes.get(self.admin_context, resource_id)
            LOG.info("The volume current state:%s" % volume.status)
            if volume.status == constants.VOLUME_AVAILABLE:
                return True
            elif volume.status == constants.VOLUME_ERROR:
                raise monitor.ResourceFailureError('Error Volume state')
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait()

    def execute(self, job_id, resource_id, volume, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入数据卷到数据库"))
        managers.volumes.update(self.admin_context, resource_id, **{
            'volume_uuid': volume['id']
        })

        self.update_job_state_desc(job_id, _(u"正在创建数据卷"))
        # 等待通知改变状态
        self._wait_volume_create(resource_id)

        self.update_job_state_desc(job_id, _(u"存入数据卷到数据库成功"))
        self.update_job_state_desc(job_id, _(u"创建数据卷成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"创建数据卷失败"))


def get_create_data_volume_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreateVolumeTask(), PersistentDataVolume())
    return flow


class DataVolumeCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(DataVolumeCreateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_create_data_volume_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        reservations = QUOTAS.reserve(self.context,
                                      **{'volumes': kwargs["size"]}
        )
        
        try:
            volume = managers.volumes.create(self.context.user_id, **kwargs)
        except Exception as err:
            LOG.info("Create volume faild: %s." % err)
            QUOTAS.rollback(self.context, reservations)
            raise err
        else:
            QUOTAS.commit(self.context, reservations)

        return volume

    def associate_resource_with_job(self, resource, job):
        managers.volumes.update(self.context, resource.id, job_id=job.id)
