# -*- coding: utf-8 -*-
from novaclient import exceptions as host_exc
from taskflow.patterns import linear_flow

from nebula.core import constants
from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients.nova import get_client as get_nova_client
from nebula.core.openstack_clients import cml
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = 'host:create'


class CreateHostTask(task.NebulaTask):
    default_provides = 'host'

    def __init__(self):
        super(CreateHostTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, host_ip, **kwargs):
        self.update_job_state_desc(job_id, _(u"验证主机资源"))

        rv = get_nova_client().servers.add_compute_node(
            ip=host_ip,
        )

        LOG.info(rv)
        self.update_job_state_desc(job_id, _(u"更新主机状态"))

        return rv

    def revert(self, job_id, resource_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        host = kwargs['result']
        # 回滚, 需要将主机状态置为disabled
        if self.is_current_task_ok(host):
            get_nova_client().servers.\
                check_disable_compute_node(host['hostname'])
        else:
            self.update_job_state_desc(job_id, _(u"添加主机失败"))
        #回滚主机状态
        managers.compute_nodes.update(self.admin_context,
                                      resource_id,
                                      {'status': constants.HOST_STATUS_ERROR})


class AddHost(task.NebulaTask):
    def __init__(self):
        super(AddHost, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, host, **kwargs):
        self.update_job_state_desc(job_id, _(u"存入数据库"))

        values = dict(
            os_hostname=host['hostname'],
            vcpus=host['cpu']['cores'],
            memory_mb=host['mem']['total'],
            local_gb=host['disk']['available'],
            cpu_info=host['cpu'],
            status=constants.HOST_STATUS_ACTIVE
        )
        managers.compute_nodes.update(self.admin_context,
                                      resource_id,
                                      values)
        self.update_job_state_desc(job_id, _(u"添加主机成功,检查集群操作"))

    def revert(self, job_id, resource_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"添加主机失败"))


class AddHostToAggregate(task.NebulaTask):
    """
    添加主机到集群的任务
    NOTE:是否与集群本身的任务合并？
    """
    def __init__(self):
        super(AddHostToAggregate, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, host, host_aggregate, **kwargs):

        LOG.info("aggregate_id = %s", host_aggregate)
        #未选择的值是-1
        if host_aggregate != -1:
            self.update_job_state_desc(job_id, _(u"正在加入集群"))

            #得到集群数据
            aggregate = managers.aggregates.get(self.admin_context,
                                                host_aggregate)
            """
             NOTE:为了健壮，以后这里需要检查是否存在和集群的状态
            """
            if aggregate is not None:
                get_nova_client().servers.\
                    add_host_aggregate(aggregate.aggregate_uuid,
                                       host['hostname'])

                self.update_job_state_desc(job_id, _(u"正在保存数据"))
                managers.compute_nodes.update(self.admin_context,
                                              resource_id,
                                              {'aggregate_id': host_aggregate})

                self.update_job_state_desc(job_id, _(u"添加主机并加入集群成功"))
            else:
                self.update_job_state_desc(job_id, _(u"要操作的集群不存在，请重新添加集群"))
        else:
            self.update_job_state_desc(job_id, _(u"无集群操作，添加主机成功"))

    def revert(self, job_id, resource_id,*args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"加入集群失败，请重新加入集群"))
        #回滚主机状态
        managers.compute_nodes.update(self.admin_context,
                                      resource_id,
                                      {'status': constants.HOST_STATUS_ERROR})


class RegisterHostToCMLTask(task.NebulaTask):

    default_provides = 'register_result'

    def __init__(self):
        super(RegisterHostToCMLTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        """
        注册主机到cml

        :param job_id: job id
        :param resource_id: 主机ID
        :param kwargs:
        :return:
        """
        # 注册监控系统失败, 不回滚虚拟机创建操作.
        try:
            host_ref = managers.compute_nodes.get(self.admin_context,
                                                  resource_id)

            cml_client = cml.get_client()
            rv = cml_client.register_vm(host_ref.id,
                                        host_ref.host_ip,
                                        os_type=None,
                                        type="HOST")
            return rv
        except Exception as ex:
            self.get_logger(**kwargs).exception(ex)
            self.get_logger(**kwargs).warning(u"注册主机到监控系统失败")


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(CreateHostTask(),         # 创建主机
             AddHost(),                # 添加数据库
             AddHostToAggregate(),     # 添加到集群
             RegisterHostToCMLTask())  # 注册到监控
    return flow


class HostCreateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None, **kwargs):
        super(HostCreateBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(
            kwargs
        )
        return managers.compute_nodes.create(self.context.user_id, **kwargs)

    def associate_resource_with_job(self, resource, job):
        managers.compute_nodes.update(self.context,
                                      resource.id,
                                      dict(job_id=job.id))
