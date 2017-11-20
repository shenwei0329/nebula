# -*- coding: utf-8 -*-

from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.common.openstack import vm_states, task_states
from nebula.core.mission import task
from nebula.core.openstack_clients import nova
from nebula.core.resource_monitor import monitor as res_mon
from nebula.core.i18n import _
from nebula.core.quota import QUOTAS

from .base import InstanceURDBuilder
import logging
LOG = logging.getLogger(__name__)


ACTION = 'instance:backup'


class QuotaOverflow(Exception):
    pass


class BackupInstanceTask(task.NebulaTask):

    default_provides = 'instance_backup'

    def __init__(self):
        super(BackupInstanceTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, instance_uuid, backup_name, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始创建虚拟机备份"))
        # get vm's old status from database.
        context = self.get_request_context(**kwargs)
        instance = managers.instances.get_by_uuid(context, instance_uuid)
        if (instance["vm_state"] != "active") or (instance['task_state'] is not None):
            self.update_job_state_desc(job_id, _(u"虚拟机正在执行其他任务，不能创建备份"))
            raise Exception(u"VM is now dealing with another task.")

        resources = ['instance_backups']
        user_id = instance.owner_id

        user_quotas = QUOTAS.get_by_user(context,
                                         user_id,
                                         resources)
        instance_backup_quota = user_quotas['instance_backups']
        instance_backup_limit = instance_backup_quota["limit"]

        backups = instance.backups
        exist_backup_num = 0
        if backups:
            for item in backups:
                exist_backup_num += 1
        if instance_backup_limit <= exist_backup_num:
            self.update_job_state_desc(job_id, _(u"配额不足，不能创建虚拟机备份"))
            raise QuotaOverflow(u"Quota to VM's backup is overflow.")

        # update vm's status in database when start to backup it.
        update_status = dict(vm_state=vm_states.BACKUP_DISK,
                             task_state=task_states.BACKUP_DISK)
        managers.instances.update_by_uuid(context, instance_uuid, update_status)
        # real backup action now, it returns a VMBackup class object
        backup = nova.get_client().servers.create_backup_v2(instance_uuid,
                                                            backup_name)
        # LOG.info("BackupInstanceTask @@@@@@@@@@@@@@ backup info: %s |||" % backup._info)
        values = dict(
            backup_uuid=backup._info['id'],
            name=backup_name,
            status='saving'
        )
        managers.instance_backups\
            .create_by_instance_backup_uuid(self.get_request_context(**kwargs),
                                            backup._info['instance_uuid'],
                                            **values)

        def checker():
            backup_ref = managers.instance_backups.get_by(
                self.admin_context, backup_uuid=backup._info['id'])
            if not backup_ref:
                # 严重错误, 没有找到相应实体
                self.update_job_state_desc(job_id, _(u"创建虚拟机备份失败"))
                raise res_mon.ResourceFailureError(u'Can not find backup object.')
            elif backup_ref.status == 'error':
                self.update_job_state_desc(job_id, _(u"创建虚拟机备份失败"))
                raise res_mon.ResourceFailureError(u"Backup instance error.")
            elif backup_ref.status == 'active':
                return True
            return False

        monitor = res_mon.ResourceChangeMonitor(checker)
        # 等待Resize完成或者错误(包括超时)
        monitor.wait()
        self.update_job_state_desc(job_id, _(u"创建虚拟机备份成功"))
        # reset vm's status to active through updating database data.
        update_status = dict(vm_state=vm_states.ACTIVE, task_state=None)
        managers.instances.update_by_uuid(self.get_request_context(**kwargs),
                                          instance_uuid,
                                          update_status)
        return backup._info

    def revert(self, job_id, instance_uuid, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        result = kwargs['result']

        #删除已创建的备份脏数据
        if result:
            if hasattr(result, "__getitem__"):
                nova.get_client().servers.delete_backup_v2(result['instance_uuid'],
                                                   result['id'])
                #删除以创建的数据库脏数据
                managers.instance_backups.delete_by_uuid(self.get_request_context(**kwargs), result['id'])
                self.update_job_state_desc(job_id, _(u"创建虚拟机备份失败"))

                update_status = dict(vm_state=vm_states.ACTIVE, task_state=None)
                managers.instances.update_by_uuid(self.get_request_context(**kwargs),
                                              instance_uuid,
                                              update_status)
            else:
                if isinstance(result.exception, QuotaOverflow):
                    self.update_job_state_desc(job_id, _(u"配额不足，不能创建虚拟机备份"))
                else:
                    self.update_job_state_desc(job_id, _(u"创建虚拟机备份失败"))
        else:
            self.update_job_state_desc(job_id, _(u"创建虚拟机备份失败"))


class BackupQueryTask(task.NebulaTask):

    default_provides = 'backup'

    def execute(self, job_id, instance_backup, *args, **kwargs):

        if instance_backup is None:
            return None

        self.update_job_state_desc(job_id, _(u"开始读取备份信息"))
        backup = nova.get_client()\
            .servers.get_backup_v2(instance_backup["instance_uuid"],
                                   instance_backup["id"])
        return backup._info

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, _(u"读取备份信息失败"))
        #BackupInstanceTask会回滚，此处不做任何回滚操作
        self.update_job_state_desc(job_id, _(u"创建虚拟机备份失败"))


class PersistentBackupTask(task.NebulaTask):

    def execute(self, job_id, backup, instance_uuid, *args, **kwargs):
        if backup is None:
            return None

        self.update_job_state_desc(job_id, _(u"开始同步数据库"))
        request_context = self.get_request_context(**kwargs)
        creator_id = request_context.user_id
        values = dict(
            status=backup['backup_status'],
            size=backup['backup_size'],
            creator_id=creator_id
        )
        managers.instance_backups\
            .update_by_backup_uuid(self.get_request_context(**kwargs),
                                   backup['id'],
                                   values)
        self.update_job_state_desc(job_id, _(u"创建虚机备份成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, _(u"获取虚机信息失败"))
        # BackupInstanceTask会回滚，此处不做任何回滚操作
        self.update_job_state_desc(job_id, _(u"创建虚拟机备份失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        BackupInstanceTask(),
        BackupQueryTask(),
        PersistentBackupTask(),
    )
    return flow


class InstanceBackupBuilder(InstanceURDBuilder):

    def __init__(self, context, resource_kwargs=None, store=None):
        super(InstanceBackupBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            store=store)

    def prepare_resource(self, *args, **kwargs):
        instance = managers.instances\
            .get(self.context,
                 kwargs["id"] or kwargs['backup_instance_id'])
        self.store.update(dict(
            instance_uuid=instance.instance_uuid,
            backup_name=kwargs["name"]))
        return instance

    def associate_resource_with_job(self, resource, job):
        managers.instances.update(self.context,
                                  resource.id,
                                  dict(job_id=job.id))


