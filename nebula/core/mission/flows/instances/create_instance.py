# -*- coding: utf-8 -*-
from novaclient import exceptions as nova_exc
from taskflow.patterns import linear_flow
import logging
from nebula.core import constants
from nebula.core.common.openstack import vm_states
from nebula.core.managers import managers
from nebula.core.quota import QUOTAS
from nebula.core.mission import flow_builder
from nebula.core.mission import task
from nebula.core.openstack_clients import neutron
from nebula.core.openstack_clients import nova
from nebula.core.openstack_clients import cml
from nebula.core.resource_monitor import monitor as res_mon
from nebula.core.i18n import _
import arrow

from nebula.core.openstack_clients. \
    cinder import get_client as get_cinder_client

LOG = logging.getLogger(__name__)

ACTION = 'instance:create'


class QueryOrCreateFlavorTask(task.NebulaTask):
    default_provides = 'flavor'

    def __init__(self):
        super(QueryOrCreateFlavorTask, self).__init__(addons=[ACTION])

    @staticmethod
    def _get_or_create_flavor(flavor_name, vcpus, ram_gb, root_gb=0):
        """创建或获取OpenStack的Flavor."""
        try:
            flavor = nova.get_client().flavors.get(flavor_name)
        except nova_exc.NotFound:
            flavor = nova.get_client().flavors.create(flavor_name,
                                                      ram_gb * 1024,
                                                      vcpus,
                                                      root_gb,
                                                      flavorid=flavor_name)
        return flavor

    def execute(self, job_id, flavor_name, vcpus, ram,
                root_gb, **kwargs):

        self.update_job_state_desc(job_id, _(u"开始获取规格"))
        flavor = self._get_or_create_flavor(flavor_name, vcpus, ram, root_gb)
        flavor_ref = managers.flavors.create_or_get(self.admin_context,
                                                    flavor.name,
                                                    flavor.vcpus,
                                                    ram, root_gb)
        self.update_job_state_desc(job_id, _(u"获取规格成功"))
        flavor_result = flavor_ref.to_dict()
        flavor_result.update({'flavor_uuid': flavor.id})
        return flavor_result

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)

        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, _(u'获取镜像失败'))
        # Flavor不需要考虑回滚

#先占用数据卷以免被影响即将创建的虚机挂载改卷
class QueryAttachVolumeTask(task.NebulaTask):

    default_provides = 'volume_attach'

    def __init__(self):
        super(QueryAttachVolumeTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, volume_uuid, **kwargs):
        LOG.info("create_instances_1:::::")
        LOG.info(volume_uuid)
        if volume_uuid:
            self.update_job_state_desc(job_id, _(u"开始挂载数据卷"))
            params = dict(
                status=constants.VOLUME_IN_USE,
                Bootable=True,
                attach_time=arrow.utcnow().to('+08:00').format('YYYY-MM-DD HH:mm:ss')
            )
            managers.volumes.update_by_uuid(self.admin_context, volume_uuid, **params)
            
            self.update_job_state_desc(job_id, _(u"申请挂载数据卷成功"))
        return volume_uuid

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        # 回滚, 更新数据库记录
        volume_uuid = kwargs.get('volume_uuid')
        print ("volume_uuid::::::::")
        #iso虚机创建失败可能会删掉相关数据卷
        if volume_uuid:
            try:
                get_cinder_client().volumes.get(volume_id=volume_uuid)
                params = dict(
                    status=constants.VOLUME_AVAILABLE
                )
                managers.volumes.update_by_uuid(self.admin_context, volume_uuid, **params)
            except Exception as err:
                volume_info=managers.volumes.get_by(self.admin_context, **{'volume_uuid':volume_uuid})
                user_id = kwargs.get('user_id')
                request_context = self.get_request_context(**kwargs)
                #释放volume资源
                reservation_volume = QUOTAS.reserve(
                    request_context,
                    user_id=user_id,
                    **{'volumes': -volume_info.size}
                )
                
                try:
                    managers.volumes.delete_by(id=volume_info.id)
                except Exception as err:
                    LOG.info("Delete instance volume faild: %s" % str(err))
                    QUOTAS.rollback(request_context, reservation_volume, user_id=user_id)
                    raise err
                else:
                    QUOTAS.commit(request_context, reservation_volume, user_id=user_id)
            self.update_job_state_desc(job_id, _(u"挂载数据卷失败"))  

class QuerySubnetByUUIDTask(task.NebulaTask):
    default_provides = 'subnet'

    def __init__(self):
        super(QuerySubnetByUUIDTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, subnet_uuid, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始获取子网"))
        subnet = managers.subnets.get_by(self.admin_context,
                                         subnet_uuid=subnet_uuid)
        return subnet.to_dict()

    def revert(self, job_id, *args, **kwargs):
        # 因为这个Task只负责查询, 因此不用考虑回滚的问题
        self.log_current_task_failures(*args, **kwargs)

        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, _(u"获取子网失败"))


class QueryNetworkFromSubnetTask(task.NebulaTask):
    default_provides = 'network'

    def __init__(self):
        super(QueryNetworkFromSubnetTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, subnet, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始获取网络"))
        network = managers.private_networks.get(self.admin_context,
                                                subnet['network_id'])
        return network.to_dict()

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, _(u"获取网络失败"))
        # 因为这个Task只负责查询, 因此不用考虑清理的问题


class CreateOSPortTask(task.NebulaTask):
    """在OpenStack环境中创建网卡."""
    default_provides = 'os_port'

    def __init__(self):
        super(CreateOSPortTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, ip_address, mac_address, security_group_uuid,
                bandwidth_tx, bandwidth_rx, network, subnet, **kwargs):

        self.update_job_state_desc(job_id, _(u"开始创建网卡"))
        port_create_options = {
            'network_id': network['network_uuid'],

        }

        fixed_ip_options = {
            'subnet_id': subnet['subnet_uuid'],
        }
        if ip_address:
            fixed_ip_options['ip_address'] = ip_address
        port_create_options['fixed_ips'] = [fixed_ip_options]

        if mac_address:
            port_create_options['mac_address'] = mac_address

        if security_group_uuid:
            security_group_options = [security_group_uuid]
            port_create_options['security_groups'] = security_group_options

        if bandwidth_tx is not None:
            port_create_options['bandwidth_tx'] = bandwidth_tx
        if bandwidth_rx is not None:
            port_create_options['bandwidth_rx'] = bandwidth_rx

        result = neutron.get_client().create_port({
            'port': port_create_options,
        })
        os_port = result['port']
        return os_port

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        # 回滚, 需要删除这个网卡
        os_port = kwargs['result']
        if self.is_current_task_ok(os_port):
            self.get_logger(**kwargs).info(
                _("Deleting port, port_id=%s"),
                os_port['id'])
            neutron.get_client().delete_port(os_port['id'])
        else:
            self.update_job_state_desc(job_id, _(u"创建网卡失败"))


class SaveOSPortToDatabaseTask(task.NebulaTask):
    default_provides = 'port'

    def __init__(self):
        super(SaveOSPortToDatabaseTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, network, subnet,
                os_port, security_group_uuid, **kwargs):

        self.update_job_state_desc(job_id, _(u"开始保存网卡信息"))

        port = managers.ports.create_(
            self.admin_context,
            port_uuid=os_port['id'],
            name=os_port['name'],
            mac_address=os_port['mac_address'],
            bandwidth_rx=os_port['bandwidth_rx'],
            bandwidth_tx=os_port['bandwidth_tx'],
            #mtu=os_port['mtu'],
            fixed_ips=os_port['fixed_ips'],
            device_id=os_port['device_id'],
            device_owner=os_port['device_owner'],
            network_id=network['id'],
            subnet_id=subnet['id'],
            instance_id=resource_id,
            creator_id=self.get_request_context(**kwargs).user_id,
            owner_id=self.get_request_context(**kwargs).user_id,
        )
        return port.to_dict()

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        # 回滚, 删除数据库记录
        port = kwargs['result']
        if self.is_current_task_ok(port):
            managers.ports.delete(port['id'])
        else:
            self.update_job_state_desc(job_id, _(u"保存网卡信息失败"))


class PersistentUpdatePortTask(task.NebulaTask):

    default_provides = 'persitent_update_port'

    def __init__(self):
        super(PersistentUpdatePortTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, port, security_group_uuid, **kwargs):
        if security_group_uuid:
            self.update_job_state_desc(job_id, _(u"应用安全组到网卡"))

            security_group = managers.security_groups.get_by_uuid(
                self.get_request_context(**kwargs),
                security_group_uuid,
            )

            managers.ports.update(self.admin_context,
                                  port['id'],
                                  security_group_id=security_group.id)

            self.update_job_state_desc(job_id, _(u"应用安全组成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, _(u"应用安全组失败"))


class CreateOSInstanceTask(task.NebulaTask):
    default_provides = 'os_instance'

    def __init__(self):
        super(CreateOSInstanceTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, display_name, display_description,
                image, flavor, subnet, port, network, volume_uuid,
                availability_zone, **kwargs):

        # 正式创建虚拟机
        # 这里需要等待虚拟机创建完成
        self.update_job_state_desc(job_id,  _(u"开始创建虚拟机"))

        nics = [{'port-id': port['port_uuid'],
                 'net-id': network['network_uuid']}]
       
        if volume_uuid:
           LOG.info("create_instances_2:::::")
           block_device_mapping_v2 =[{'source_type': u'volume',
                                       'delete_on_termination': True,
                                       'uuid': volume_uuid,
                                       'destination_type': u'volume'}]
           instance = nova.get_client().servers.create(block_device_mapping_v2=block_device_mapping_v2,
               name=display_name, image=image['image_uuid'], flavor=flavor['flavor_uuid'],
               nics=nics, availability_zone=availability_zone)
        else:
           LOG.info("create_instances_3:::::")
           instance = nova.get_client().servers.create(
                display_name, image['image_uuid'], flavor['flavor_uuid'],
                nics=nics, availability_zone=availability_zone)
        
        instance_uuid = instance.id

        # 更新数据库资源
        managers.instances.update_by_id(
            self.admin_context,
            resource_id,
            {
                'memory_mb': flavor['memory_mb'],
                'vcpus': flavor['vcpus'],
                'root_gb': flavor['root_gb'],
                'ephemeral_gb': flavor['ephemeral_gb'],
                'instance_uuid': instance_uuid,
            })
        
        # 更新volume数据库资源
        if volume_uuid:
            LOG.info("create_instances_2.2:::::")
            LOG.info(instance.id)
            LOG.info(resource_id)
            params = dict(
                 instance_id=resource_id
            )
            managers.volumes.update_by_uuid(self.admin_context, volume_uuid, **params)

        def checker():
            instance_ref = managers.instances.get_by(
                self.admin_context, instance_uuid=instance_uuid)
            if not instance_ref:
                # 严重错误, 没有找到相应实体
                raise res_mon.ResourceFailureError('Entity not found')
            elif instance_ref['vm_state'] == vm_states.ERROR:
                raise res_mon.ResourceFailureError('Error VM state')
            elif instance_ref['vm_state'] == vm_states.ACTIVE \
                    and instance_ref['compute_node_id']:
                # 状态为 active, 创建完成
                return True
            return False


        monitor = res_mon.ResourceChangeMonitor(checker)

        # 等待完成或者错误(包括超时)
        if image and image['disk_format'].lower() == "vmdk":
            monitor.wait(3600)
        else:
            monitor.wait()

        self.update_job_state_desc(job_id, _(u"创建虚拟机成功"))

        return instance.to_dict()

    def revert(self, job_id, *args, **kwargs):
        # 回滚, 但是不删除虚拟机, 错误的虚拟机应该由用户删除
        if self.is_current_task_failed(kwargs['result']):
            self.update_job_state_desc(job_id, _(u"创建虚拟机失败"))


class RegisterVMToCMLTask(task.NebulaTask):

    default_provides = 'register_result'

    def __init__(self):
        super(RegisterVMToCMLTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, os_instance, image, **kwargs):
        """
        注册虚拟机到cml

        :param job_id: job id
        :param resource_id: 虚拟机ID
        :param image: 镜像内容
        :param port: 网卡内容
        :param kwargs:
        :return:
        """
        # 注册监控系统失败, 不回滚虚拟机创建操作.
        try:
            instance_ref = managers.instances.get(self.admin_context,
                                                  resource_id)

            cml_client = cml.get_client()
            rv = cml_client.register_vm(os_instance['id'],
                                        instance_ref.compute_node.host_ip,
                                        os_type=image['architecture'])
            self.get_logger(**kwargs).info(u"注册到监控系统成功")
            return rv
        except Exception as ex:
            self.get_logger(**kwargs).exception(ex)
            self.get_logger(**kwargs).warning(u"注册到监控系统失败")


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(QueryOrCreateFlavorTask(),
             QueryAttachVolumeTask(),
             QuerySubnetByUUIDTask(),
             QueryNetworkFromSubnetTask(),
             CreateOSPortTask(),
             SaveOSPortToDatabaseTask(),
             PersistentUpdatePortTask(),
             CreateOSInstanceTask()
             #RegisterVMToCMLTask()
             )
    return flow


class InstanceCreateBuilder(flow_builder.Builder):
    def __init__(self, context, resource_kwargs=None, store=None):
        super(InstanceCreateBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            store=store)

    def associate_resource_with_job(self, resource, job):
        managers.instances.update(self.context, resource.id, dict(job_id=job.id))

    def prepare_resource(self, *args, **kwargs):
        resources = dict(
            cores=kwargs['vcpus'],
            ram=kwargs['ram'] * 1024,
            instances=1
        )

        availability_zone = None
        if kwargs['zone']:
            availability_zone = kwargs['zone']

        kwargs.update({'availability_zone': availability_zone})
        
        # iso_image install get volume_id
        volume_uuid = kwargs.get('volume_uuid')
        
        self.store.update(kwargs)
        # get image
        image_uuid = kwargs['image_uuid']
        image_obj = managers.images.get_by(
            self.context,
            image_uuid=image_uuid)
        self.store.update({'image': image_obj.to_dict()})
        # get flavor
        flavor_name = 'vcpus_%d-ram_%d-disk_%d' % (kwargs['vcpus'],
                                                   kwargs['ram'],
                                                   image_obj.min_disk)

        flavor_obj = managers.flavors.create_or_get(self.context,
                                                    flavor_name,
                                                    kwargs['vcpus'],
                                                    kwargs['ram'],
                                                    image_obj.min_disk)

        self.store.update({
            'flavor_name': flavor_name,
            'root_gb': image_obj.min_disk,
            'volume_uuid': volume_uuid,
            'user_id':self.context.user_id
        })

        reservations = QUOTAS.reserve(self.context, **resources)
        assert reservations is not None, "reservations must not be none"
        try:
            instance = managers.instances.create(
                self.context,
                image_id=image_obj.id,
                flavor_id=flavor_obj.id,
                display_name=kwargs['display_name'],
                display_description=kwargs['display_description'],
                vm_state=vm_states.BUILDING,
                creator_id=self.context.user_id,
                owner_id=self.context.user_id,
            )
        except Exception as err:
            LOG.info("Create instance faild: %s." % str(err))
            QUOTAS.rollback(
                self.context,
                kwargs['reservations']
            )
            raise err
        else:
            QUOTAS.commit(self.context, reservations)

        return instance
