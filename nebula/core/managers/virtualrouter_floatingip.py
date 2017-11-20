# -*- coding: utf-8 -*-

from nebula.core.managers.base import BaseManager
from nebula.core.models import VirtualrouterFloatingIP


class VirtualrouterFloatingIPManager(BaseManager):

    def _get(self, context, floatingip_id, session=None):
        return self.model_query(
            context, VirtualrouterFloatingIP, session=session, user_only=False
        ).filter_by(id=floatingip_id).first()

    def get(self, context, floatingip_id):
        return self._get(context, floatingip_id)

    def get_by(self, context, **params):
        return self.model_query(
            context, VirtualrouterFloatingIP
        ).filter_by(**params).first()

    def get_all_by(self, context, **params):
        return self.model_query(
            context, VirtualrouterFloatingIP
        ).filter_by(**params).all()

    def create(self, uuid, floating_ip, creator_id, floating_network_id,
               fixed_ip=None, virtualrouter_id=None, owner_id=None):
        if not owner_id:
            owner_id = creator_id
        with self.transactional() as session:
            virtualrouter_floatingip = VirtualrouterFloatingIP(
                floatingip_uuid=uuid,
                floating_ip_address=floating_ip,
                floating_network_id=floating_network_id,
                fixed_ip_address=fixed_ip,
                virtualrouter_id=virtualrouter_id,
                creator_id=creator_id,
                owner_id=owner_id
            )
            virtualrouter_floatingip.save(session)
        return virtualrouter_floatingip

    def get_or_create(self, context, uuid, floating_ip, creator_id, floating_network_id,
                      fixed_ip=None, virtualrouter_id=None, owner_id=None):

        floating_ips = self.get_by(context, floating_ip_address=floating_ip)
        if not floating_ips:
            return self.create(context, uuid, floating_ip, creator_id, floating_network_id,
                               fixed_ip, virtualrouter_id, owner_id)
        else:
            return floating_ips[0]

    def update(self, context, floatingip_id, values):
        with self.transactional() as session:
            floatingip = self._get(context, floatingip_id, session=session)
            floatingip.update(values)

    def update_router(self, context, network_id, user_id, router_id):
        with self.transactional() as session:
            floatingips = self.model_query(context, VirtualrouterFloatingIP).\
                filter_by(floating_network_id=network_id, owner_id=user_id).all()

            for floatingip in floatingips:
                self.update(context, floatingip.id, dict(virtualrouter_id=router_id))


    '''
    def _amount_queryset(self, context, is_binding=False,
                         is_unbind=False, owner_id=None):

        assert not (is_binding and is_unbind), u'is_binding与is_unbind不能同时为True'

        query = VirtualrouterFloatingip.query
        if owner_id is not None:
            query = query.filter(VirtualrouterFloatingip.owner_id == owner_id)

        if is_binding:
            query = query.filter(VirtualrouterFloatingip.virtualrouter != None)

        if is_unbind:
            query = query.filter(VirtualrouterFloatingip.virtualrouter == None)
        return query

    def _total_amount_queryset(self, context, owner_id=None):
        return self._amount_queryset(context, owner_id=owner_id)

    def _unbinding_amount_queryset(self, context, owner_id=None):
        return self._amount_queryset(context, owner_id=owner_id, is_unbind=True)

    def _binding_amount_queryset(self, context, owner_id=None):
        return self._amount_queryset(context, owner_id=owner_id, is_binding=True)

    def amount(self, context, owner_id=None):
        return self._total_amount_queryset(context, owner_id).count()

    def unbinding_amount(self, context, owner_id=None):
        return self._unbinding_amount_queryset(context, owner_id).count()

    def binding_amount(self, context, owner_id=None):
        return self._binding_amount_queryset(context, owner_id).count()

    def unbinding_publicips(self, context, owner_id=None):
        return self._unbinding_amount_queryset(context, owner_id).all()
    '''

    def delete(self, floating_ip_id):
        result = dict(
            code=1,
            message=u'success'
        )
        with self.transactional() as session:
            floating_ip = session.query(VirtualrouterFloatingIP).\
                filter(VirtualrouterFloatingIP.id == floating_ip_id).first()
            if not floating_ip:
                result.update(dict(
                    code=0,
                    message=u'Not Found Public Ip.'
                ))
                return result
            if floating_ip.virtualrouter_id:
                result.update(dict(
                    code=0,
                    message=u'Bind Virtual Router, Can not Delete.'
                ))
                return result
            session.delete(floating_ip)
        return result

    def stat_by_user(self, context, user_id=None):
        ret = dict()
        if not user_id:
            user_id = context.user_id
        with self.transactional() as session:
            query = session.query(VirtualrouterFloatingIP).\
                filter(VirtualrouterFloatingIP.owner_id == user_id)
            limit = query.count()
            usages = query.\
                filter(VirtualrouterFloatingIP.virtualrouter_id != None).count()
            ret.update(dict(
                limit=limit,
                usages=dict(
                    total=usages
                )
            ))
        return ret

    def stat_all(self):
        ret = dict()
        with self.transactional() as session:
            query = session.query(VirtualrouterFloatingIP).filter()
            total = query.count()
            usages = query\
                .filter(VirtualrouterFloatingIP.virtualrouter_id != None)\
                .count()
            ret.update(dict(
                total=total,
                usages=usages
            ))
        return ret
