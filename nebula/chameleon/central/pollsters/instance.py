# coding=utf-8
import six

from nebula.core.managers import managers
from nebula.chameleon.central import plugin
from nebula.core.openstack_clients import nova
from nebula.core.db import session as db_session
from nebula.core.context import get_admin_context
from nebula.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class InstanceStatus(plugin.CentralPollster):
    """
    同步虚拟机状态. 推荐任务轮询时间: 5分钟.
    """
    def poll(self, manager, cache):
        instances = nova.get_client().servers.list()
        instance_uuid_to_status = {}
        for instance in instances:
            LOG.info('* get vm: <instance(%s) vm_state=%s, task_state=%s, host=%s>',
                     instance.id,
                     getattr(instance, 'OS-EXT-STS:vm_state'),
                     getattr(instance, 'OS-EXT-STS:task_state'),
                     getattr(instance, 'OS-EXT-SRV-ATTR:host'))

            instance_uuid_to_status[instance.id] = {
                'vm_state': getattr(instance, 'OS-EXT-STS:vm_state'),
                'task_state': getattr(instance, 'OS-EXT-STS:task_state'),
                'host': getattr(instance, 'OS-EXT-SRV-ATTR:host'),
            }


        context = get_admin_context()
        for instance_uuid, state_dict in six.iteritems(instance_uuid_to_status):
            try:
                if state_dict['host']:
                    host = state_dict.pop('host')
                    compute_node_ref = managers.compute_nodes.get_by_hostname(context, host)
                    state_dict.update({'compute_node_id': compute_node_ref.id})
                    managers.instances.update_by_uuid(context, instance_uuid, state_dict)
            except Exception as ex:
                LOG.exception(ex)


# class InstanceSync(plugin.CentralPollster):
#     """
#     同步虚拟机数据. 推荐任务轮询时间: 30分钟
#     """
#     def poll(self, manager, cache):
#         instances = nova.get_client().list()
#         instance_uuids = {instance.id for instance in instances}
