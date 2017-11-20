# -*- coding: utf-8 -*-

from taskflow import retry
from taskflow.patterns import linear_flow
import logging
from nebula.core.managers import managers
from nebula.core.mission import flow_builder
from nebula.core.mission import task
from nebula.core.openstack_clients import nova
from nebula.core.openstack_clients import glance
from nebula.core.i18n import _

LOG = logging.getLogger(__name__)

ACTION = 'instanceBackup:modify'


class UpdateInstanceBackup(task.NebulaTask):
    def __init__(self):
        super(UpdateInstanceBackup, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, backup_uuid, backup_name,
                instance_uuid, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始更新后台备份"))
        #glance.get_client().images.update(backup_uuid, name=backup_name)
        nova.get_client().servers.rename_backup_v2(instance_uuid,
                                                   backup_uuid,
                                                   backup_name)

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, u'更新后台备份失败')


class UpdateInstanceBackUpRecord(task.NebulaTask):
    def __init__(self):
        super(UpdateInstanceBackUpRecord, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, backup_uuid, backup_name, **kwargs):
        #managers.images.update(self.context, resource_id=resource_id, name=backup_name)
        values = dict(
            name=backup_name
        )
        request_context = self.get_request_context(**kwargs)
        managers.instance_backups.update(request_context,
                                         resource_id,
                                         values=values)
        self.update_job_state_desc(job_id, _(u"更新备份成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, u'更新前台备份失败')


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(UpdateInstanceBackup(), UpdateInstanceBackUpRecord())
    return flow


class UpdateInstanceBackUpBuilder(flow_builder.Builder):
    def __init__(self, context, resource_kwargs=None, store=None):
        super(UpdateInstanceBackUpBuilder, self).__init__(
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
        self.store.update({'backup_uuid': record.backup_uuid,
                           'backup_name': kwargs['name'],
                           'instance_uuid': '12345687'})   # 接口已修改，该参数已失效
        return record
