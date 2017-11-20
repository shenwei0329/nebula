# -*- coding: utf-8 -*-
import copy
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
ACTION = 'host:sync'


HOST_ENTITY = {"hostname": "",
               "host_ip": "",
               "zone": "",
               "state": "",
               "updated_at": "",
               "hypervisor_type": "",
               "os_hostname": "",
               "vcpus": "",
               "vcpus_used": "",
               "memory_mb": "",
               "memory_mb_used": "",
               "local_gb": "",
               "local_gb_used": "",
               "cpu_info": "",
               "status": "",
               }


class HostSyncTask(task.NebulaTask):
    default_provides = 'hosts'

    def __init__(self):
        super(HostSyncTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"获取计算主机列表"))
        try:
            services = get_nova_client().services.list()
        except Exception as ex:
            LOG.error("Openstack services service is not available")
            self.update_job_state_desc(job_id, _(u"获取计算主机失败"))
            raise ex

        comput_host = [service for service in services if service.binary == "nova-compute"]

        if len(comput_host) > 0:
            try:
                hypervisors = get_nova_client().hypervisors.list()
            except Exception as ex:
                LOG.error("Openstack hypervisors is not available")
                self.update_job_state_desc(job_id, _(u"获取计算主机失败"))
                raise ex
            ret_hosts = []
            for host in comput_host:
                ins_host = copy.copy(HOST_ENTITY)
                for hypervisor in hypervisors:
                    if hypervisor.service.get("host") == host.host:
                        ins_host["hostname"] = hypervisor.hypervisor_hostname
                        ins_host["host_ip"] = hypervisor.host_ip
                        ins_host["zone"] = host.zone
                        ins_host["state"] = host.state
                        ins_host["updated_at"] = host.updated_at
                        ins_host["hypervisor_type"] = hypervisor.hypervisor_type
                        ins_host["os_hostname"] = hypervisor.service.get("host")
                        ins_host["vcpus"] = hypervisor.vcpus
                        ins_host["vcpus_used"] = hypervisor.vcpus_used
                        ins_host["memory_mb"] = hypervisor.memory_mb
                        ins_host["memory_mb_used"] = hypervisor.memory_mb_used
                        ins_host["local_gb"] = hypervisor.local_gb
                        ins_host["local_gb_used"] = hypervisor.local_gb_used
                        ins_host["cpu_info"] = hypervisor.cpu_info
                        ins_host["status"] = (constants.HOST_STATUS_MAINTAIN if host.status == "disabled" else constants.HOST_STATUS_ACTIVE)
                        ret_hosts.append(ins_host)
                        break

            LOG.info("[sync_host] get openstack %s data" % len(ret_hosts))
            return ret_hosts

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"同步计算主机失败"))


class UpdateOldHostTask(task.NebulaTask):
    default_provides = 'new_hosts'
    def __init__(self):
        super(UpdateOldHostTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, hosts, **kwargs):
        self.update_job_state_desc(job_id, _(u"更新已存在的数据"))
        old_hosts = managers.compute_nodes.all()
        update_num = 0

        ##更新已存在的数据
        for ohost in old_hosts:
            for i, nhost in enumerate(hosts):
                if ohost.os_hostname == nhost.get("os_hostname") and ohost.host_ip == nhost.get("host_ip"):
                    #更新时，不更新门户的主机名字
                    nhost["hostname"] = ohost.hostname
                    #更新数据
                    managers.compute_nodes.update(self.admin_context, ohost.id, nhost)
                    hosts.remove(nhost)
                    update_num += 1
        LOG.info("[sync_host] update %s data" % update_num)
        return hosts

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"同步计算主机失败"))

class UpdateNewHostTask(task.NebulaTask):
    default_provides = 'add_hosts'
    def __init__(self):
        super(UpdateNewHostTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, new_hosts, **kwargs):
        add_host = []
        self.update_job_state_desc(job_id, _(u"处理新增的数据"))
        ##新增新的主机列表
        if len(new_hosts) >= 1:
            add_host = managers.compute_nodes.creates(new_hosts)
        LOG.info("[sync_host] add %s data" % len(new_hosts))
        self.update_job_state_desc(job_id, _(u"同步计算主机成功"))
        return add_host


    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"同步计算主机失败"))

class RegisterHostToCMLTask(task.NebulaTask):

    default_provides = 'register_result'

    def __init__(self):
        super(RegisterHostToCMLTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, add_hosts, **kwargs):
        """
        注册主机到cml

        :param job_id: job id
        :param resource_id: 主机ID
        :param kwargs:
        :return:
        """
        # 注册监控系统失败, 不回滚虚拟机创建操作.
        try:
            LOG.info("[sync_host] Register CML %s data" % len(add_hosts))
            for host in add_hosts:
                cml_client = cml.get_client()
                rv = cml_client.register_vm(host.id,
                                            host.host_ip,
                                            os_type=None,
                                            type="HOST")
                LOG.info("[sync_host] Register CML %s  ret=%s" % (host.host_ip, rv))
        except Exception as ex:
            self.get_logger(**kwargs).exception(ex)
            self.get_logger(**kwargs).warning(u"注册主机到监控系统失败")
    def revert(self, job_id, *args, **kwargs):
        pass


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(HostSyncTask(), UpdateOldHostTask(), UpdateNewHostTask(), RegisterHostToCMLTask())
    return flow


class HostSyncBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None, **kwargs):
        super(HostSyncBuilder, self).__init__(
            context, resource_args=resource_args,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        user = managers.users.get_by_username("root")
        return user

    def associate_resource_with_job(self, resource, job):
        pass
