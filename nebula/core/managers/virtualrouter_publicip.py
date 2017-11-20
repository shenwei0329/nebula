# -*- coding: utf-8 -*-

from nebula.core.managers.base import BaseManager
from nebula.core.models import VirtualrouterPublicIP


class VirtualrouterPublicIPManager(BaseManager):

    def _get(self, context, publicip_id, session=None):
        return self.model_query(
            context, VirtualrouterPublicIP, session=session, user_only=False
        ).filter_by(id=publicip_id).first()

    def get(self, context, publicip_id):
        return self._get(context, publicip_id)

    def get_by(self, context, **params):
        return self.model_query(
            context, VirtualrouterPublicIP
        ).filter_by(**params).all()

    def create(self, context, public_ip, creator_id, mask, gateway_ip, owner_id=None):
        if not owner_id:
            owner_id = creator_id
        with self.transactional() as session:
            virtualrouter_publicip = VirtualrouterPublicIP(
                public_ip=public_ip,
                mask=mask,
                gateway_ip=gateway_ip,
                creator_id=creator_id,
                owner_id=owner_id
            )
            virtualrouter_publicip.save(session)
        return virtualrouter_publicip

    def get_or_create(self, context, public_ip, creator_id, mask,
                      gateway_ip, owner_id=None):

        public_ips = self.get_by(context, public_ip=public_ip)
        if not public_ips:
            return self.create(context, public_ip, creator_id, mask, gateway_ip, owner_id)
        else:
            return public_ips[0]

    def update(self, context, publicip_id, values):
        with self.transactional() as session:
            publicip = self._get(context, publicip_id, session=session)
            publicip.update(values)

    def _amount_queryset(self, context, is_binding=False,
                         is_unbind=False, owner_id=None):

        assert not (is_binding and is_unbind), u'is_binding与is_unbind不能同时为True'

        query = VirtualrouterPublicIP.query
        if owner_id is not None:
            query = query.filter(VirtualrouterPublicIP.owner_id == owner_id)

        if is_binding:
            query = query.filter(VirtualrouterPublicIP.virtualrouter != None)

        if is_unbind:
            query = query.filter(VirtualrouterPublicIP.virtualrouter == None)
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

    def delete(self, public_ip_id):
        result = dict(
            code=1,
            message=u'success'
        )
        with self.transactional() as session:
            public_ip = session.query(VirtualrouterPublicIP).\
                filter(VirtualrouterPublicIP.id == public_ip_id).first()
            if not public_ip:
                result.update(dict(
                    code=0,
                    message=u'Not Found Public Ip.'
                ))
                return result
            if public_ip.virtualrouter_id:
                result.update(dict(
                    code=0,
                    message=u'Bind Virtual Router, Can not Delete.'
                ))
                return result
            session.delete(public_ip)
        return result

    def stat_by_user(self, context, user_id=None):
        ret = dict()
        if not user_id:
            user_id = context.user_id
        with self.transactional() as session:
            query = session.query(VirtualrouterPublicIP).\
                filter(VirtualrouterPublicIP.owner_id == user_id)
            limit = query.count()
            usages = query.\
                filter(VirtualrouterPublicIP.virtualrouter_id != None).count()
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
            query = session.query(VirtualrouterPublicIP).filter()
            total = query.count()
            usages = query\
                .filter(VirtualrouterPublicIP.virtualrouter_id != None)\
                .count()
            ret.update(dict(
                total=total,
                usages=usages
            ))
        return ret
