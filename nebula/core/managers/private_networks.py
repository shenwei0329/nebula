# -*- coding: utf-8 -*-

from nebula.core.managers.base import BaseManager
from nebula.core.models import Network


class NetworkManager(BaseManager):

    def _get(self, context, private_network_id, session=None):
        return self.model_query(context, Network,
                                session=session, user_only=False).filter_by(id=private_network_id).first()

    def get(self, context, private_network_id):
        return self._get(context, private_network_id)

    def get_by(self, context, **kwargs):
        return self.model_query(context, Network, **kwargs) \
                   .filter_by(**kwargs) \
                   .first()

    def get_external_network(self, context):
        #return self.model_query(context, Network).filter_by(external_net=True).all()
        with self.transactional() as session:
            return session.query(Network).filter_by(external_net=True).all()

    def get_by_all(self, context, **kwargs):
        return self.model_query(context, Network, **kwargs) \
                   .filter_by(**kwargs) \
                   .all()

    def create(self, creator, **kwargs):
        with self.transactional() as session:
            net = Network(
                name=kwargs.get("name", "default"),
                description=kwargs.get("description", None),
                network_type=kwargs.get("network_type", "vlan"),
                physical_network=kwargs.get("physical_network", "default"),
                segmentation_id=kwargs["segmentation_id"],
                external_net=kwargs.get("external_net"),
                shared=kwargs.get("shared", False),
                status="build",
                creator_id=creator,
                owner_id=creator)
            net.save(session)
        return net

    def update(self, context, private_network_id, **values):
        with self.transactional() as session:
            private_network = self._get(context, private_network_id, session)
            private_network.update(values)
        return private_network

    def delete_by(self, **kwargs):
        with self.transactional() as session:
            session.query(Network).filter_by(**kwargs).delete()

    def all(self, context, **kwargs):
        return self.model_query(context, Network, **kwargs).all()

    def availables(self, context, **kwargs):
        return self.model_query(context, Network, **kwargs)\
            .filter(Network.network_uuid != None).all()

    def count_all(self):
        with self.transactional() as session:
            result = session.query(Network).filter().count()
        return result or 0

    def count_ext_net_all(self):
        with self.transactional() as session:
            result = session.query(Network).filter_by(external_net=True).count()
        return result or 0

    def count_int_net_all(self):
        with self.transactional() as session:
            result = session.query(Network).filter_by(external_net=False).count()
        return result or 0

    def get_internal_network(self, context, **kwargs):
        internal_nets = self.model_query(context, Network, **kwargs)\
            .filter(Network.network_uuid != None).filter(Network.external_net==False).all()

        if not context.is_super:
            with self.transactional() as session:
                flat_net = session.query(Network).filter_by(network_type='flat').all()
                if flat_net is not None:
                    internal_nets.extend(flat_net)
        else:
            available_nets = []
            for net in internal_nets:
                if net.owner_id == context.user_id:
                    available_nets.append(net)
            internal_nets = available_nets

        return internal_nets
