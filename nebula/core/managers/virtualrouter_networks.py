# -*- coding: utf-8 -*-
from sqlalchemy.orm import joinedload

from nebula.core.managers.base import BaseManager
from nebula.core.models import VirtualrouterNetwork
from nebula.core.models import VirtualrouterSubnet

class VirtualrouterNetworkManager(BaseManager):

    def _get(self, context, virtualrouter_network_id, session=None):
        return self.model_query(context, VirtualrouterNetwork, session=session, user_only=False).\
            filter_by(id=virtualrouter_network_id).first()

    def get(self, context, virtualrouter_network_id):
        return self._get(context, virtualrouter_network_id)

    def filter_by(self, **kwargs):
        with self.transactional() as session:
            return session.query(VirtualrouterNetwork).filter_by(**kwargs)

    def get_by(self, context, **params):
        return self.model_query(
            context, VirtualrouterNetwork
        ).filter_by(**params).first()

    def create(self, creator, **kwargs):
        with self.transactional() as session:
            vn = VirtualrouterNetwork(
                network_id=kwargs["network_id"],
                virtualrouter_id=kwargs["virtualrouter_id"],
                virtualrouter_network_uuid=kwargs["virtualrouter_network_uuid"],
                creator_id=creator,
                owner_id=creator)
            vn.save(session)
        return vn

    def update(self, context, virtualrouter_network_id, **values):
        with self.transactional() as session:
            private_network = self._get(context,
                                        virtualrouter_network_id, session)
            private_network.update(values)
        return private_network

    def delete_by(self, **kwargs):
        with self.transactional() as session:
            session.query(VirtualrouterNetwork).filter_by(**kwargs).delete()




class VirtualrouterSubnetManager(BaseManager):

    def _get(self, context, virtualrouter_subnet_id, session=None):
        return self.model_query(context, VirtualrouterSubnet, session=session, user_only=False).\
            filter_by(id=virtualrouter_subnet_id).first()

    def get(self, context, virtualrouter_subnet_id):
        return self._get(context, virtualrouter_subnet_id)

    def filter_by(self, context, **kwargs):
        with self.transactional() as session:
            return session.query(VirtualrouterSubnet).filter_by(**kwargs)

    def create(self, creator, **kwargs):
        with self.transactional() as session:
            vn = VirtualrouterSubnet(
                subnet_id=kwargs["subnet_id"],
                virtualrouter_id=kwargs["virtualrouter_id"],
                virtualrouter_subnet_uuid=kwargs["virtualrouter_subnet_uuid"],
                creator_id=creator,
                owner_id=creator)
            vn.save(session)
        return vn

    def update(self, context, virtualrouter_subnet_id, **values):
        with self.transactional() as session:
            private_subnet = self._get(context,
                                        virtualrouter_subnet_id, session)
            private_subnet.update(values)
        return private_subnet

    def delete_by(self, **kwargs):
        with self.transactional() as session:
            session.query(VirtualrouterSubnet).filter_by(**kwargs).delete()