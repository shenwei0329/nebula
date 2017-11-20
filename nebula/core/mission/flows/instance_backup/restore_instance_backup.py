# -*- coding: utf-8 -*-

from taskflow import retry
from taskflow.patterns import linear_flow
import logging
from nebula.core.managers import managers
from nebula.core.mission import flow_builder
from nebula.core.mission import task
from nebula.core.openstack_clients import nova
from nebula.core.openstack_clients import glance
from nebula.core.common.openstack import vm_states
from nebula.core.common.openstack import task_states
from nebula.core.resource_monitor import monitor
from nebula.core.i18n import _


LOG = logging.getLogger(__name__)

ACTION = 'instanceBackup:restore'


class RevertInstanceBackUpFind(task.NebulaTask):
    def __init__(self):
        super(RevertInstanceBackUpFind, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, instance_uuid,
                backup_uuid, **kwargs):

        self.update_job_state_desc(job_id, _(u"开始查询指定虚拟机备份"))
        nova.get_client().servers.get_backup_v2(instance_uuid, backup_uuid)
        self.update_job_state_desc(job_id, _(u"查询指定虚拟机备份成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, u'查询指定虚拟机备份失败')

        # 只是查询instance_backup是否存在，因此不需要考虑回滚


class RevertInstanceBackup(task.NebulaTask):
    def __init__(self):
        super(RevertInstanceBackup, self).__init__(addons=[ACTION])

    def _wait_revert_instancebackup(self, job_id, instance_uuid, **kwargs):
        """等待虚机恢复完成，然后真正恢复(通过消息改变状态后)."""

        def checker():
            LOG.info("RevertInstanceBackup_2.1:::::")
            instance = managers.instances.get_by_uuid(self.admin_context,
                                                      instance_uuid)
            LOG.info("RevertInstanceBackup_2:::::")
            LOG.info(instance)
            if instance.vm_state == u'active':
                return True
            elif instance.vm_state == u'error':
                raise res_mon.ResourceFailureError(
                    'Error InstanceBackup Restore state')
            return False
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait()

        self.update_job_state_desc(job_id, _(u"虚拟机恢复成功"))

    def execute(self, job_id, resource_id, backup_uuid,
                instance_uuid, **kwargs):

        self.update_job_state_desc(job_id, _(u"开始虚拟机恢复"))
        
        #恢复虚机前先锁定虚机状态
        values = dict(
            vm_state=vm_states.RESCUED
        )
        new_instance_ref = managers\
            .instances.update_by_uuid(self.admin_context,
                                    instance_uuid,
                                    values)
        
        nova.get_client().servers.restore_backup_v2(instance_uuid, backup_uuid)
        LOG.info("RevertInstanceBackup_1:::::")
        LOG.info(instance_uuid)
        self._wait_revert_instancebackup(job_id, instance_uuid)

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, u'后台虚拟机恢复失败')

        # 虚机恢复失败，情况非常复杂，建议手动回滚


class RevertInstanceBackUpRecord(task.NebulaTask):
    def __init__(self):
        super(RevertInstanceBackUpRecord, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, backup_uuid, **kwargs):
        values = dict(
            backup_uuid=backup_uuid
        )
        request_context = self.get_request_context(**kwargs)
        managers.instance_backups.update(request_context,
                                         resource_id,
                                         values=values)
        self.update_job_state_desc(job_id, _(u"虚拟机恢复成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, u'前台虚拟机恢复失败')


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(RevertInstanceBackUpFind(),
             RevertInstanceBackup(),
             RevertInstanceBackUpRecord()
             )
    return flow


class InstanceBackUpRevertBuilder(flow_builder.Builder):
    def __init__(self, context, resource_kwargs=None, store=None):
        super(InstanceBackUpRevertBuilder, self).__init__(
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
        LOG.info("prepare_resource_1::::::::::::")
        LOG.info(record)
        self.store.update({'backup_uuid': record.backup_uuid,
                           'instance_uuid': record.instance.instance_uuid})
        return record
