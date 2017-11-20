# -*- coding: utf-8 -*-


from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder

from nebula.openstack.common import log
from nebula.core.common.openstack import vm_states
from nebula.core.i18n import _
from nebula.core.resource_monitor import monitor
from nebula.core.openstack_clients import nova
from nebula.core.openstack_clients import cml

LOG = log.getLogger(__name__)
ACTION = "instance:migrate"


class ComputeNodeResourcesJudg(task.NebulaTask):
    #由于虚机资源属于动态变化，因此需再次判断该目的主机资源是否满足虚机要求
    default_provides = 'compute_node_info'

    def __init__(self):
        super(ComputeNodeResourcesJudg, self).__init__(addons=[ACTION])

    def execute(self, job_id, compute_node_id, instance_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始验证计算节点资源情况"))

        #获取该虚机详细信息
        instance_info = managers.instances.get(self.admin_context, instance_id)
        if instance_info is None:
            self.update_job_state_desc(job_id, _(u"虚拟机不存在"))
            raise Exception(("Error Instance is not exist"))

        #获取该虚机配置信息
        instance_flavor_info = managers.flavors.get(self.admin_context,
                                                    instance_info.flavor_id)
        if instance_info is None:
            self.update_job_state_desc(job_id, _(u"虚拟机flavor不存在"))
            raise Exception(("Error Instance_Flavor is not exist"))

        #获取该迁移节点详细信息
        compute_info = managers.compute_nodes.get(self.admin_context,
                                                  compute_node_id)
        if compute_info is None:
            self.update_job_state_desc(job_id, _(u"迁移目标主机不存在"))
            raise Exception(("Error Dest_Computenode is not exist"))
        else:
            LOG.info("ComputeNodeResourcesJudg_24::::::::")
            LOG.info(compute_info.left_memory_mb)
            LOG.info(instance_flavor_info.memory_mb)
            if (compute_info.left_memory_mb >= instance_flavor_info.memory_mb):
                self.update_job_state_desc(job_id, _(u"迁移目标主机内存配额满足要求"))
            else:
                self.update_job_state_desc(job_id, _(u"迁移目标主机内存配额不满足要求"))
                raise Exception(("Error Dest_Computenode_resource is unexpected"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)


class InstanceMigrateTask(task.NebulaTask):

    def __init__(self):
        super(InstanceMigrateTask, self).__init__(addons=[ACTION])

    def _wait_instance_migrate(self, job_id, instance_uuid, **kwargs):
        """等待虚机迁移完成(通过消息改变状态)."""
        def checker():
            instance = managers.instances.get_by_uuid(self.admin_context,
                                                      instance_uuid)
            if instance.vm_state == 'active':
                if instance.task_state is None:
                    return True
                else :
                    return False
            elif instance.vm_state == 'error':
                raise res_mon.ResourceFailureError('Error InstanceBackup ConvertImage state')
            return False
        res_mon = monitor.ResourceChangeMonitor(checker)
        res_mon.wait()
        self.update_job_state_desc(job_id, _(u"虚拟机迁移成功"))

    def execute(self, job_id, instance_id, compute_node_id, **kwargs):
        #获取该虚机详细信息
        instance_info = managers.instances.get(self.admin_context, instance_id)

        #获取该迁移节点详细信息
        compute_info = managers.compute_nodes.get(self.admin_context,
                                                  compute_node_id)

        #将该虚机状态从active->migrating,同时将计算节点置为目的节点
        values = dict(vm_state=vm_states.MIGRATE,
                      compute_node_id=compute_info.id,
                      task_state='migrating')
        managers.instances.update_by_id(self.admin_context, instance_id, values)

        nova.get_client().servers.live_migrate(instance_info.instance_uuid,
                                               compute_info.os_hostname,
                                               block_migration=False,
                                               disk_over_commit=False)
        self.update_job_state_desc(job_id, _(u"虚拟机开始迁移"))
        self._wait_instance_migrate(job_id, instance_info.instance_uuid)
        return instance_info.compute_node_id

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        #将该虚机状态从migrating->active,同时将虚机所在计算节点写回原计算节点
        values = dict(vm_state=vm_states.ACTIVE,
                      compute_node_id=kwargs['compute_node_id'],
                      task_state=None)
        managers.instances.update_by_id(self.admin_context, kwargs['instance_id'], values)

        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, u'虚拟机迁移失败 ')


class ModifyVMToCMLTask(task.NebulaTask):

    default_provides = 'Modify_result'

    def __init__(self):
        super(ModifyVMToCMLTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        """
        修改虚拟机到cml

        :param job_id: job id
        :param resource_id: 虚拟机ID
        :param kwargs:
        :return:
        """
        # 修改监控数据失败, 不回滚虚拟机迁移操作.
        try:
            instance_ref = managers.instances.get(self.admin_context,
                                                  resource_id)

            cml_client = cml.get_client()
            rv = cml_client.modify_vm(instance_ref.instance_uuid,
                                      instance_ref.compute_node.host_ip,
                                      os_type=None)
            return rv
        except Exception as ex:
            self.get_logger(**kwargs).exception(ex)
            self.get_logger(**kwargs).warning(u"修改虚拟机到监控系统失败")


def get_migrate_data_instance_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        ComputeNodeResourcesJudg(),
        InstanceMigrateTask(),
        ModifyVMToCMLTask())
    return flow


class DataMigrateBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(DataMigrateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_migrate_data_instance_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(dict(
            instance_id=kwargs["resource_id"],
            compute_node_id=kwargs["compute_node_id"]
        ))
        return managers.instances.get(self.context, kwargs["resource_id"])

    def associate_resource_with_job(self, resource, job):
        # 更新虚拟机的任务状态
        managers.instances.update(self.context,
                                  resource.id,
                                  dict(job_id=job.id))
