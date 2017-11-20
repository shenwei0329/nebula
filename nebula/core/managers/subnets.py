# -*- coding: utf-8 -*-
from sqlalchemy.orm import joinedload
from nebula.openstack.common import jsonutils
from nebula.core.managers.base import BaseManager
from nebula.core.models import Subnet


class SubnetManager(BaseManager):

    def _get(self, context, subnet_id, session=None):
        return self.model_query(context, Subnet, session=session, user_only=False).\
            options(joinedload(Subnet.network)).filter_by(id=subnet_id).first()

    def get(self, context, subnet_id):
        return self._get(context, subnet_id)

    def get_by(self, context, **kwargs):
        return self.model_query(context, Subnet) \
                   .filter_by(**kwargs) \
                   .first()

    def create(self, creator, **kwargs):
        with self.transactional() as session:
            subnet = Subnet(
                network_id=kwargs["network_id"],
                subnet_uuid=kwargs["subnet_uuid"],
                name=kwargs["name"],
                cidr=kwargs["cidr"],
                gateway_ip=kwargs["gateway_ip"],
                dns_nameservers=kwargs["dns_nameservers"],
                allocation_pools=kwargs["allocation_pools"],
                host_routes=kwargs["host_routes"],
                description=kwargs["description"],
                creator_id=creator,
                owner_id=creator
            )
            subnet.save(session)
        return subnet

    def update(self, context, subnet_id, **values):
        with self.transactional() as session:
            subnet = self._get(context, subnet_id, session)
            subnet.update(values)

    def delete_by(self, **kwargs):
        with self.transactional() as session:
            session.query(Subnet).filter_by(**kwargs).delete()
