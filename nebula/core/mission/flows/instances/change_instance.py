# -*- coding: utf-8 -*-
from novaclient import exceptions as nova_exc
from taskflow.patterns import linear_flow

from nebula.core.common.openstack import vm_states
from nebula.core.managers import managers
from nebula.core.mission import flow_builder
from nebula.core.mission import task
from nebula.core.openstack_clients import nova
from nebula.core.resource_monitor import monitor as res_mon
from nebula.core.i18n import _
from nebula.core.quota import QUOTAS

from . import create_instance

import logging
LOG = logging.getLogger(__name__)

ACTION = 'instance:change-flavor'


class QueryOrCreateFlavorTask(create_instance.QueryOrCreateFlavorTask):
    def __init__(self):
        task.NebulaTask.__init__(self, addons=[ACTION])


class ChangeOSInstanceTask(task.NebulaTask):
    def __init__(self):
        super(ChangeOSInstanceTask, self).__init__()

    def execute(self, job_id, resource_id, reservations, user_id, instance_uuid, flavor, **kwargs):
        self.update_job_state_desc(job_id, _(u"正在更新虚拟机规格"))
        try:
            nova.get_client().servers.resize(instance_uuid, flavor['name'])
        except nova_exc.BadRequest as ex:
            LOG.error(ex)
            self.update_job_state_desc(job_id, _(u"目标主机资源不满足修改配置要求"))
            raise Exception(_("Error:compute node resource is overflow"))

        def checker():
            instance_ref = managers.instances.get_by(
                self.admin_context, instance_uuid=instance_uuid)
            if not instance_ref:
                # 严重错误, 没有找到相应实体
                raise res_mon.ResourceFailureError('Entity not found')
            elif instance_ref['vm_state'] == vm_states.ERROR:
                raise res_mon.ResourceFailureError('Error VM state')
            elif instance_ref['vm_state'] == vm_states.RESIZED:
                return True
            elif instance_ref['vm_state'] == vm_states.ACTIVE:
                return True
            return False

        monitor = res_mon.ResourceChangeMonitor(checker)
        # 等待Resize完成或者错误(包括超时)
        monitor.wait()
        self.update_job_state_desc(job_id, _(u"修改虚拟机配置成功"))

    def revert(self, job_id, instance_uuid, reservations, user_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        try:
            # 失败的话, 尝试调用一次 REVERT RESIZE, 撤销上次的操作
            self.update_job_state_desc(job_id, _(u"修改虚拟机配置失败"))
            QUOTAS.rollback(self.get_request_context(**kwargs), reservations, user_id=user_id)
            #nova.get_client().servers.revert_resize(instance_uuid)
        except nova_exc.ClientException as err:
            logger = self.get_logger(**kwargs)
            logger.error(err)


class ModifyInstanceEntityTask(task.NebulaTask):
    default_provides = ('old_instance', 'new_instance')

    def execute(self, resource_id, flavor, reservations, user_id, **kwargs):
        # 更新数据库中虚拟机条目
        old_instance_ref = managers.instances.get(self.admin_context,
                                                  resource_id)
        old_instance = old_instance_ref.to_dict()

        values = dict(
            vcpus=flavor['vcpus'],
            memory_mb=flavor['memory_mb'],
            flavor_id=flavor['id']
        )
        new_instance_ref = managers\
            .instances.update_by_id(self.admin_context,
                                    resource_id,
                                    values)
        new_instance = new_instance_ref.to_dict()
        QUOTAS.commit(self.get_request_context(**kwargs), reservations, user_id=user_id)
        return old_instance, new_instance

    def revert(self, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        result = kwargs['result']
        if self.is_current_task_ok(result):
            old_instance, _ = result

            values = dict(
                vcpus=old_instance['vcpus'],
                memory_mb=old_instance['memory_mb'],
                flavor_id=old_instance['flavor_id']
            )
            managers.instances.update_by_id(self.admin_context,
                                            kwargs['resource_id'],
                                            values)


class ChangeOSInstanceConfirmationTask(task.NebulaTask):
    def __init__(self):
        super(ChangeOSInstanceConfirmationTask, self).__init__(addons=[ACTION])

    def execute(self, instance_uuid, **kwargs):
        nova.get_client().servers.confirm_resize(instance_uuid)

    def revert(self, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(
        QueryOrCreateFlavorTask(),
        ChangeOSInstanceTask(),
        ModifyInstanceEntityTask(),
        #ChangeOSInstanceConfirmationTask()
    )
    return flow


class InstanceChangeBuilder(flow_builder.Builder):
    def __init__(self, context, resource_kwargs=None, store=None):
        super(InstanceChangeBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            store=store)

    def associate_resource_with_job(self, resource, job):
        managers.instances.update(self.context, resource.id, dict(job_id=job.id))

    def prepare_resource(self, *args, **kwargs):
        # get flavor
        flavor_name = 'vcpus_%d-ram_%d-disk_%d' % (kwargs['vcpus'],
                                                   kwargs['ram'],
                                                   kwargs.get('root_gb', 0))
        old_instance_ref = managers.instances.get(self.context,
                                                  kwargs["resource_id"])
        old_instance = old_instance_ref.to_dict()

        data = dict(
            instance_uuid=kwargs['instance_uuid'],
            vcpus=kwargs['vcpus'],
            ram=kwargs['ram'],
            root_gb=kwargs.get('root_gb', 0),
            flavor_name=flavor_name,
        )

        delta = dict(
            vcpus=0,
            ram=0
        )
        
        delta['vcpus'] = kwargs['vcpus'] - old_instance["vcpus"]
        delta['ram'] = kwargs['ram'] * 1024 - old_instance["memory_mb"]

        self.store.update(data)

        resources = dict(
            cores=delta['vcpus'],
            ram=delta['ram'],
        )
        reservations = QUOTAS.reserve(self.context, user_id=old_instance_ref.owner_id, **resources)

        self.store.update({
            'reservations': reservations,
            'user_id': old_instance_ref.owner_id,
        })
        return managers.instances.get(self.context, kwargs['resource_id'])
