# -*- coding: utf-8 -*-

import logging

from taskflow import retry
from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import flow_builder
from nebula.core.mission import task
from nebula.core.openstack_clients import nova
from nebula.core.resource_monitor import monitor as res_mon
from nebula.core.i18n import _

LOG = logging.getLogger(__name__)

ACTION = 'instanceBackup:delete'


class DeleteInstanceBackup(task.NebulaTask):
    default_provides = 'instance_backup'

    def __init__(self):
        super(DeleteInstanceBackup, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除虚拟机备份"))
        record = managers.\
            instance_backups.get(self.get_request_context(**kwargs),
                                 resource_id)
        LOG.info("DeleteInstanceBackup_1:::::::::::")
        LOG.info(record)
        if record is None:
            self.update_job_state_desc(job_id, _(u"该虚拟机备份底层不存在"))
            managers.instance_backups.delete_by_id(self.admin_context,
                                                   resource_id)
            raise Exception('Error Instance_Backup exist')
        elif not record.status:
            self.update_job_state_desc(job_id, _(u"虚拟机有备份任务正在执行"))
            raise Exception('Error Instance_Backup has job')
        
        instance_uuid = '12345678' #底层接口已修改，该参数已失效
        
        try:
            nova.get_client().servers.delete_backup_v2(instance_uuid,
                                                       record.backup_uuid)
        except:
            LOG.info("DeleteOSImageBackups_2")
            managers.instance_backups.delete_by_id(self.admin_context,
                                                   resource_id)
            
        instance_info = dict(
            instance_uuid=instance_uuid,
            backup_uuid=record.backup_uuid
        )
        return instance_info

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"删除虚机备份失败"))


class DeleteInstanceBackUpRecord(task.NebulaTask):
    def __init__(self):
        super(DeleteInstanceBackUpRecord, self).__init__(addons=[ACTION])

    def execute(self, job_id, instance_backup, resource_id, **kwargs):
        update_values = dict(status='deleted')
        managers.instance_backups\
            .update_by_backup_uuid(self.get_request_context(**kwargs),
                                   instance_backup['backup_uuid'],
                                   update_values)
        
        def checker():
            backup_ref = managers.instance_backups.get_by(
                self.admin_context, backup_uuid=instance_backup['backup_uuid'])
            if backup_ref is None:
                # 严重错误, 没有找到相应实体
                return True
            elif backup_ref.status == 'error':
                raise res_mon.ResourceFailureError('Error instance backups state')
            return False

        monitor = res_mon.ResourceChangeMonitor(checker)
        # 等待Resize完成或者错误(包括超时)
        monitor.wait()
        self.update_job_state_desc(job_id, _(u"删除备份成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeleteInstanceBackup(), DeleteInstanceBackUpRecord())
    return flow


class DeleteInstanceBackUpBuilder(flow_builder.Builder):
    def __init__(self, context, resource_kwargs=None, store=None):
        super(DeleteInstanceBackUpBuilder, self).__init__(
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
        return record
