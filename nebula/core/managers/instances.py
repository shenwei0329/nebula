# -*- coding: utf-8 -*-

import logging

from sqlalchemy.sql import func, column

from nebula.core import models
from nebula.core.context import is_user_context

from .base import BaseManager


LOG = logging.getLogger(__name__)


class InstanceManager(BaseManager):
    def _get(self, context, id, session=None):
        if not session:
            session = self.get_session()
        return self.model_query(context, models.Instance, session=session, user_only=False) \
                   .get(id)

    def get(self, context, id):
        return self._get(context, id)

    def get_by(self, context, **kwargs):
        LOG.info("get")
        LOG.info(kwargs)
        return self.model_query(context, models.Instance) \
                   .filter_by(**kwargs) \
                   .first()

    def _get_by_uuid(self, context, instance_uuid, session=None):
        if not session:
            session = self.get_session()
        return self.model_query(context, models.Instance, session=session) \
                   .filter_by(instance_uuid=instance_uuid).first()

    def get_by_uuid(self, context, instance_uuid):
        return self._get_by_uuid(context, instance_uuid)

    def create(self, context, **kwargs):
        with self.transactional() as session:
            instance = models.Instance(**kwargs)
            instance.save(session)
            return instance

    def _delete_by(self, context, values):
        with self.transactional() as session:
            self.model_query(context, models.Instance, session=session, user_only=False) \
                .filter_by(**values) \
                .delete()

    def delete_by(self, context, values):
        return self._delete_by(context, values)

    def delete_by_id(self, context, id):
        return self._delete_by(context, dict(id=id))

    def delete_by_uuid(self, context, instance_uuid):
        return self._delete_by(context, dict(instance_uuid=instance_uuid))

    def update(self, context, instance_id, values):
        with self.transactional() as session:
            instance = self._get(context, instance_id, session=session)
            instance.update(values)
        return instance

    def update_by_uuid(self, context, instance_uuid, values):
        LOG.info("update_by_uuid_1::::")
        LOG.info(values)
        with self.transactional() as session:
            instance_ref = self._get_by_uuid(context, instance_uuid,
                                             session=session)
            if instance_ref:
                instance_ref.update(values)
                instance_ref.save(session)
        return instance_ref

    def update_by_id(self, context, id, values):
        with self.transactional() as session:
            instance_ref = self._get(context, id, session=session)
            instance_ref.update(values)
            instance_ref.save(session)
        return instance_ref
        
    def all(self, context, is_oneself=False, **kwargs):
        return self.image_query(context, is_oneself=is_oneself, **kwargs).all()

    def image_query(self, context, is_oneself=False, **kwargs):
        query = self.model_query(context, models.Instance, user_only=False)
        if is_oneself:
            if is_user_context(context):
                query = query.filter_by(owner_id=context.user_id)
            else:
                query = query.filter(column('owner_id') != None)
        else:
            query = query.filter_by(owner_id=None)
        return query

    def count_all(self):
        with self.transactional() as session:
            result = session.query(models.Instance).filter().count()
        return result or 0

    def sum_cores(self):
        with self.transactional() as session:
            result = session.query(func.sum(models.Instance.vcpus)).scalar()
        return result or 0

    def sum_ram(self):
        with self.transactional() as session:
            result = session.query(func.sum(models.Instance.memory_mb)).scalar()
        return result or 0

    def sum_disk(self):
        with self.transactional() as session:
            result = session.query(func.sum(models.Instance.root_gb)).scalar()
        return result or 0

    def get_avail_instances_for_ports(self, user_id, limit):
        instances = list()
        with self.transactional() as session:
            result_query = session.query(models.Instance)\
                .filter(models.Instance.vm_state == 'active')
            if user_id:
                result_query = result_query.filter(models.Instance.owner_id == user_id)
            compute_nodes = session.query(models.ComputeNode)\
                .filter(models.ComputeNode.hypervisor_type == "VMware vCenter Server").first()
            if compute_nodes:
                vmware_compute_id = compute_nodes.id
                result_query = result_query.filter(models.Instance.compute_node_id != vmware_compute_id)
            else:
                pass
            result = result_query.all()
            for item in result:
                if len(item.ports) < limit:
                    item.hard_limit = limit
                    item.usable_ports = limit - len(item.ports)
                    instances.append(item)
        return instances

    def get_ports_count(self, context, **kwargs):
        instance_id = kwargs.get('instance_id')
        with self.transactional() as session:
            instance = session.query(models.Instance)\
                .filter(models.Instance.id == instance_id,
                        owner_id=context.user_id).first()
            if instance:
                return len(instance.ports)
        return -1

    def get_backups_count(self, context, **kwargs):
        instance_id = kwargs.get('instance_id')
        with self.transactional() as session:
            instance = session.query(models.Instance)\
                .filter(models.Instance.id == instance_id,
                        owner_id=context.user_id).first()
            if instance:
                return len(instance.backups)
        return -1

