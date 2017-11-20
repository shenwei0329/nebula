# -*- coding: utf-8 -*-
from taskflow.patterns import linear_flow

from nebula.core import constants
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients.nova import get_client as get_nova_client
from nebula.core.openstack_clients.ceilometer import get_client as get_ceilometer_client
from nebula.openstack.common import log
from nebula.core.openstack_clients import cml
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = 'host:maintain'


class HostDeleteTask(task.NebulaTask):
    default_provides = 'host'

    def __init__(self):
        super(HostDeleteTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        """
        维护状态的主机，才能补删除
        :param job_id:
        :param resource_id:
        :param kwargs:
        :return:
        """
        self.update_job_state_desc(job_id, _(u"更新主机状态中"))
        #判断是否在集群中...'
        host = managers.compute_nodes.get(self.admin_context, resource_id)
        if host.aggregate:
            get_nova_client().servers.\
            remove_host_aggregate(host.aggregate.aggregate_uuid,
                                  host.os_hostname)

        managers.compute_nodes.delete_by_id(self.admin_context, resource_id)
        self.update_job_state_desc(job_id, _(u"移除主机成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"移除主机失败"))


class UnregisterHostToCMLTask(task.NebulaTask):

    def execute(self, job_id, resource_id, *args, **kwargs):
        """

        :param job_id: job id
        :param host: 主机ID
        :param args:
        :param kwargs:
        :return:
        """
        # 注销虚拟机监控失败, 不回滚主机删除操作
        try:
            cml.get_client().unregister_vm(resource_id, type="HOST")
        except Exception as ex:
            self.get_logger(**kwargs).exception(ex)


class RemoveAlarmsOnHostTask(task.NebulaTask):
    default_provides = 'alarm'

    def __init__(self):
        super(RemoveAlarmsOnHostTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):

        #self.update_job_state_desc(job_id, _(u"更新主机状态中"))

        host = managers.compute_nodes.get(self.admin_context, resource_id)
        bindings = managers.alarm_bindings.get_by(self.admin_context, instance_id=host.id)

        if bindings != None:
            for item in bindings:
                get_ceilometer_client().alarms.delete(item['alarm_cml_id'])
                managers.alarm_bindings.delete_by(alarm_cml_id=item['alarm_cml_id'])

        #self.update_job_state_desc(job_id, _(u"清理主机告警成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"清理主机告警失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(RemoveAlarmsOnHostTask(),
             HostDeleteTask(),
             UnregisterHostToCMLTask())
    return flow


class HostDeleteBuilder(Builder):

    def __init__(self, context, resource_args=(),
                 resource_kwargs=None, **kwargs):
        super(HostDeleteBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        return managers.compute_nodes.get(self.context, kwargs['resource_id'])

    def associate_resource_with_job(self, resource, job):
        managers.compute_nodes.update(self.context,
                                      resource.id,
                                      dict(job_id=job.id))
