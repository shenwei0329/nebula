# -*- coding: utf-8 -*-
from nebula.core.models import VirtualrouterNat
from nebula.core.managers.base import BaseManager


class VirtualrouterNatManager(BaseManager):

    def _get(self, context, id, session=None):
        return self.model_query(context, VirtualrouterNat,
                                session=session, user_only=False).filter_by(id=id).first()

    def get(self, context, id):
        return self._get(context, id)

    def get_by(self, context, **params):
        return self.model_query(
            context, VirtualrouterNat
        ).filter_by(**params).first()

    def get_all_by(self, context, **params):
        return self.model_query(
            context, VirtualrouterNat
        ).filter_by(**params).all()

    def create(self, user_id, floatingip_id, virtualrouter_nat_uuid,
               proto, dest_ip, dest_port=None, src_port=None):
        with self.transactional() as session:
            nat = VirtualrouterNat(
                floatingip_id=floatingip_id,
                virtualrouter_nat_uuid=virtualrouter_nat_uuid,
                proto=proto,
                dest_ip=dest_ip,
                dest_port=dest_port,
                src_port=src_port,
                creator_id=user_id,
                owner_id=user_id,
            )
            nat.save(session)
        return nat

    def update(self, context, nat_id, values):
        with self.transactional() as session:
            nat = self._get(context, nat_id, session=session)
            nat.update(values)

    def delete(self, context, nat):
        with self.transactional() as session:
            if isinstance(nat, (int, long)):
                nat = session.query(VirtualrouterNat).get(nat)
            session.delete(nat)

    def get_by(self, context, **params):
        return self.model_query(
            context, VirtualrouterNat
        ).filter_by(**params).first()