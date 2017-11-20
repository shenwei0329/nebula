# -*- coding: utf-8 -*-
import logging

from sqlalchemy import func

from nebula.core import constants
from nebula.core.models import Aggregate
from nebula.core.models import ComputeNode
from nebula.core.models import Instance
from nebula.core.managers.base import BaseManager

from nebula.core import constants

LOG = logging.getLogger(__name__)


class ComputeNodeManager(BaseManager):
    def _get(self, context, id, session=None):
        if not session:
            session = self.get_session()
        return self.model_query(context, ComputeNode, session=session, user_only=False).get(id)

    def get(self, context, id):
        return self._get(context, id)

    def all(self, session=None):
        if not session:
            session = self.get_session()
        return self.model_query({}, ComputeNode, session=session, user_only=False).all()

    def get_by_hostname(self, context, hostname):
        with self.transactional() as session:
            result = self.model_query(context, ComputeNode, session=session, user_only=False).\
                filter(ComputeNode.os_hostname == hostname).one()
            return result

    def creates(self, hosts):
        new_hosts = []
        with self.transactional() as session:
            for entity in hosts:
                host = ComputeNode(
                    hostname=entity.get("hostname"),
                    host_ip=entity.get("host_ip"),
                    zone=entity.get("zone"),
                    state=entity.get("state"),
                    updated_at=entity.get("updated_at"),
                    hypervisor_type=entity.get("hypervisor_type"),
                    os_hostname=entity.get("os_hostname"),
                    os_user=entity.get("os_user"),
                    os_user_pwd=entity.get("os_user_pwd"),
                    vcpus=entity.get("vcpus"),
                    vcpus_used=entity.get("vcpus_used"),
                    memory_mb=entity.get("memory_mb"),
                    memory_mb_used=entity.get("memory_mb_used"),
                    local_gb=entity.get("local_gb"),
                    local_gb_used=entity.get("local_gb_used"),
                    cpu_info=entity.get("cpu_info"),
                    status=entity.get("status"),
                )
                new_hosts.append(host)
            session.add_all(new_hosts)
            return new_hosts


    def create(self, creator_id, **kwargs):
        with self.transactional() as session:
            host = ComputeNode(
                hostname=kwargs.get("hostname"),
                #aggregate_id = aggregate.id,
                host_ip=kwargs.get("host_ip"),
                os_user=kwargs.get("os_user"),
                os_user_pwd=kwargs.get("os_user_pwd"),
                status=constants.HOST_STATUS_ADDING,
                creator_id=creator_id,
                owner_id=creator_id
            )
            host.save(session)
            return host

    def _delete_by(self, context, values):
        with self.transactional() as session:
            self.model_query(context, ComputeNode, session=session, user_only=False) \
                .filter_by(**values) \
                .delete()

    def delete_by_id(self, context, id):
        with self.transactional() as session:
            if isinstance(id, (int, long)):
                host = session.query(ComputeNode).get(id)
            session.delete(host)

    def get_available_hosts(self, context):
        """获取未加入集群的主机列表"""
        with self.transactional() as session:
            result = self.model_query(context, ComputeNode, session=session)\
                .filter(ComputeNode.status == constants.HOST_STATUS_ACTIVE)\
                .filter(ComputeNode.aggregate_id == None) \
                .all()
            return result

    def get_hosts_by_aggregate(self, context, aggregate_id):
        """根据集群编号获取主机列表"""
        with self.transactional() as session:
            result = self.model_query(context, ComputeNode, session=session)\
                .filter(ComputeNode.aggregate_id == aggregate_id)\
                .all()
            return result

    def update(self, context, host_id, values):
        with self.transactional() as session:
            host = self._get(context, host_id, session=session)
            host.update(values)
        return host

    def vcpu_count(self, context, **kwargs):
        """
        获取计算节点vcpu总和

        :param context:
        :return: Nebula Request Context
        """
        with self.transactional() as session:
            result = session.query(func.sum(ComputeNode.vcpus)).scalar()
            return result or 0

    def memory_mb_count(self, context, **kwargs):
        """
        获取计算节点内存总和

        :param context: Nebula Request Context
        :return:
        """
        with self.transactional() as session:
            return session.query(func.sum(ComputeNode.memory_mb)).scalar() or 0

    def local_gb_count(self, context, **kwargs):
        """
        获取计算节点本地磁盘容量总和

        :param context: Nebula Request Context
        :return:
        """
        with self.transactional() as session:
            return self.model_query(context,
                                    func.count(ComputeNode.local_gb),
                                    session).scalar()

    def get_enable_hosts(self):
        with self.transactional() as session:
            return session.query(ComputeNode).\
                filter(ComputeNode.status == constants.HOST_STATUS_ACTIVE).\
                order_by('aggregate_id').all()

    def get_host_exclude_instance(self, instance_id):
        with self.transactional() as session:
            compute_nodes = list()
            instance = session.query(Instance).\
                filter(Instance.id == instance_id).first()
            if not instance:
                return compute_nodes
            compute_nodes_query = session.query(ComputeNode).\
                filter(ComputeNode.id != instance.compute_node_id).\
                filter(ComputeNode.status == constants.HOST_STATUS_ACTIVE).\
                order_by('aggregate_id').all()
            for compute_node in compute_nodes_query:
                aggregate_id = 0
                aggregate_name = u'其他'
                if compute_node.aggregate_id:
                    aggregate_id = compute_node.aggregate_id
                    aggregate_name = compute_node.aggregate.name

                aggregate = [item for item in compute_nodes
                             if aggregate_id == item.get('id')]
                if aggregate:
                    aggregate = aggregate[0]
                    aggregate['compute_nodes'].append(dict(
                        id=compute_node.id,
                        name=compute_node.hostname
                    ))
                else:
                    aggregate = dict(
                        id=aggregate_id,
                        name=aggregate_name,
                        compute_nodes=[dict(
                            id=compute_node.id,
                            name=compute_node.hostname
                        )]
                    )
                    compute_nodes.append(aggregate)

            return compute_nodes

    def get_host_exclude_instance_vmware(self, instance_id):
        VMWARE_HOST_TYPE = 'VMware vCenter Server'

        with self.transactional() as session:
            compute_nodes = list()
            instance = session.query(Instance).\
                filter(Instance.id == instance_id).first()
            if not instance:
                return compute_nodes
            compute_nodes_query = session.query(ComputeNode).\
                filter(ComputeNode.id != instance.compute_node_id).\
                filter(ComputeNode.status == constants.HOST_STATUS_ACTIVE).\
                filter(ComputeNode.hypervisor_type != VMWARE_HOST_TYPE).\
                order_by('aggregate_id').all()
            for compute_node in compute_nodes_query:
                aggregate_id = 0
                aggregate_name = u'其他'
                if compute_node.aggregate_id:
                    aggregate_id = compute_node.aggregate_id
                    aggregate_name = compute_node.aggregate.name

                aggregate = [item for item in compute_nodes
                             if aggregate_id == item.get('id')]
                if aggregate:
                    aggregate = aggregate[0]
                    aggregate['compute_nodes'].append(dict(
                        id=compute_node.id,
                        name=compute_node.hostname
                    ))
                else:
                    aggregate = dict(
                        id=aggregate_id,
                        name=aggregate_name,
                        compute_nodes=[dict(
                            id=compute_node.id,
                            name=compute_node.hostname
                        )]
                    )
                    compute_nodes.append(aggregate)

            return compute_nodes

    def count_all(self):
        with self.transactional() as session:
            result = session.query(ComputeNode).filter().count()
            return result or 0

