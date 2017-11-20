# -*- coding: utf-8 -*-
from novaclient import exceptions as nova_exc
from taskflow.patterns import linear_flow

from nebula.core.common.openstack import vm_states
from nebula.core.managers import managers
from nebula.core.quota import QUOTAS
from nebula.core.mission import task
from nebula.core.openstack_clients import nova
from nebula.core.openstack_clients import cml
from nebula.core.resource_monitor import monitor
from nebula.core.i18n import _
from nebula.core.openstack_clients.ceilometer import get_client as get_ceilometer_client

from nebula.core.openstack_clients. \
    nova import get_client as get_nova_client

from .base import InstanceURDBuilder

ACTION = 'instance:delete'
from nebula.openstack.common import log
LOG = log.getLogger(__name__)

class DeleteOSInstanceTask(task.NebulaTask):
    def __init__(self):
        super(DeleteOSInstanceTask, self).__init__()

    def _wait_instance_deletion(self, resource_id):
        """等待虚拟机删除完成(失败、超时等)."""

        def checker():
            instance_ref = managers.instances.get(self.admin_context,
                                                  resource_id)
            if instance_ref is None:
                # Race condition. Instance already gone.
                return True

            # 在并发接受到消息后, 可能会存在task_state不能设置为None的情况
            # if instance_ref.task_state is not None:
            #     return

            if instance_ref.vm_state == vm_states.DELETED:
                return True

        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait()

    def execute(self, job_id, resource_id, instance_uuid, user_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"正在删除虚拟机"))
        
        if instance_uuid is not None:
            try:
                nova.get_client().servers.delete(instance_uuid)
                self._wait_instance_deletion(resource_id)
            except nova_exc.NotFound:
                # Race condition. Instance already gone.
                pass

    def revert(self, job_id, user_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"删除虚拟机失败"))


class DeleteInstanceEntityTask(task.NebulaTask):
    def execute(self, job_id, resource_id, user_id, volume_id, volume_size, **kwargs):
        self.update_job_state_desc(job_id, _(u"删除虚拟机记录"))
        request_context = self.get_request_context(**kwargs)

        resource = managers.instances.get(request_context, resource_id)
        cores = resource.vcpus and -resource.vcpus or 0
        ram = resource.memory_mb and -resource.memory_mb or 0
        instances = -1
        params = dict(
            cores=cores,
            ram=ram,
            instances=instances
        )

        reservations = QUOTAS.reserve(request_context,
                                      user_id=resource.owner_id,
                                      **params
        )
        try:
            # 删除数据库中虚拟机条目
            managers.instances.delete_by_id(self.admin_context, resource_id)
            #删除数据库中信息
            if volume_id:
                LOG.info("Instance volume id: %s" % volume_id)
                #释放volume资源
                reservation_volume = QUOTAS.reserve(
                    request_context,
                    user_id=user_id,
                    **{'volumes': -volume_size}
                )
                try:
                    managers.volumes.delete_by(id=volume_id)
                except Exception as err:
                    LOG.info("Delete instance volume faild: %s" % str(err))
                    QUOTAS.rollback(request_context, reservation_volume, user_id=user_id)
                    raise err
                else:
                    QUOTAS.commit(request_context, reservation_volume, user_id=user_id)
        except Exception as err:
            LOG.info("Delete instance faild: %s" % str(err))
            QUOTAS.rollback(request_context, reservations, user_id=user_id)
            raise err
        else:
            #释放instance资源
            QUOTAS.commit(request_context, reservations, user_id=user_id)

        self.update_job_state_desc(job_id, _(u"删除虚拟机成功"))

    def revert(self, job_id, user_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"删除虚拟机记录失败"))

class UnregisterVMToCMLTask(task.NebulaTask):

    def execute(self, job_id, instance_uuid, *args, **kwargs):
        """

        :param job_id: job id
        :param instance_uuid: 虚拟机UUID
        :param args:
        :param kwargs:
        :return:
        """
        # 注销虚拟机监控失败, 不回滚虚拟机删除操作
        try:
            cml.get_client().unregister_vm(instance_uuid)
        except Exception as ex:
            self.get_logger(**kwargs).exception(ex)

class RemoveAlarmsOnInstanceTask(task.NebulaTask):
    default_provides = 'alarm'

    def __init__(self):
        super(RemoveAlarmsOnInstanceTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):

        #self.update_job_state_desc(job_id, _(u"更新虚拟机告警状态中"))

        instance = managers.instances.get(self.admin_context, resource_id)
        bindings = managers.alarm_bindings.get_by(self.admin_context, instance_id=instance.instance_uuid)

        if bindings is not None:
            for item in bindings:
                get_ceilometer_client().alarms.delete(item['alarm_cml_id'])
                managers.alarm_bindings.delete_by(alarm_cml_id=item['alarm_cml_id'])

        #self.update_job_state_desc(job_id, _(u"清理虚拟机告警成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"清理虚拟机告警失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        RemoveAlarmsOnInstanceTask(),
        DeleteOSInstanceTask(),
        DeleteInstanceEntityTask()
    )
    return flow


class InstanceDeleteBuilder(InstanceURDBuilder):
    def __init__(self, context, resource_kwargs=None, store=None):
        super(InstanceDeleteBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            store=store)

    def prepare_resource(self, *args, **kwargs):
        resource = super(InstanceDeleteBuilder, self).prepare_resource(*args,
                                                                       **kwargs)
        
        #查询该虚机是否通过iso创建，如果是删除虚机的同时也要删除系统卷
        volume_info = dict(
            instance_id=resource.id,
            Bootable=True
        )
        volume = managers.volumes.get_by(self.context, **volume_info)
        if volume:
            volume_id = volume.id
            volume_size=volume.size
        else:
            volume_id = None
            volume_size = None
        self.store.update({
            'user_id': resource.owner_id,
            'volume_id': volume_id,
            'volume_size':volume_size}
        )
        return resource
