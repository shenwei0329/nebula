# -*- coding: utf-8 -*-
import random
import string

from nebula.core.managers.base import BaseManager
from nebula.core.models import Virtualrouter
from nebula.core.models import VirtualrouterNetwork
from nebula.core.common.propertyutils import cached_property

from . import cache

get_random_string = lambda y: "".join(
    map(lambda x: random.choice(string.ascii_letters), range(y)))


# TODO(xuewnbao): 此段代码只做为示例保留
class VirtualrouterCountCache(cache.CountCache):

    KEY_VIRTUALROUTER_COUNT = 'system:virtualrouter_count'
    KEY_USER_VIRTUALROUTER_COUNT = 'user:{user_id}:virtualrouter_count'

    response_callback = int

    def key(self, *args, **kwargs):
        user_id = kwargs.get('user_id')
        return self.KEY_USER_VIRTUALROUTER_COUNT.format(user_id=user_id) \
            if user_id is not None else \
            self.KEY_VIRTUALROUTER_COUNT


class VirtualrouterManager(cache.CountCacheMixin, BaseManager):

    model_class = Virtualrouter

    @cached_property
    def count_cache(self):
        return VirtualrouterCountCache(self.model_class)

    def _get(self, context, id, session=None):
        return self.model_query(context, Virtualrouter, session=session, user_only=False).\
            filter_by(id=id).first()

    def get(self, context, id):
        return self._get(context, id)

    def all(self, context, **kwargs):
        return self.model_query(context, Virtualrouter, **kwargs).all()

    def filter_by(self, **kwargs):
        with self.transactional() as session:
            return session.query(Virtualrouter).filter_by(**kwargs)

    def availables(self, context, **kwargs):
        return self.model_query(context, Virtualrouter, **kwargs).filter(
            Virtualrouter.virtualrouter_uuid != None
        ).all()

    def create(self, user_id, name=None, driver='netns', description='',
               bandwidth_tx=1, bandwidth_rx=1, ha='False', job_id=None):

        with self.transactional() as session:
            virtualrouter = Virtualrouter(name=name,
                                          description=description,
                                          bandwidth_tx=bandwidth_tx,
                                          bandwidth_rx=bandwidth_rx,
                                          creator_id=user_id,
                                          owner_id=user_id,
                                          ha=ha,
                                          job_id=job_id)
            virtualrouter.save(session)
        return virtualrouter

    def delete(self, virtualrouter):
        with self.transactional() as session:
            if isinstance(virtualrouter, (int, long)):
                virtualrouter = session.query(Virtualrouter).get(virtualrouter)
            session.delete(virtualrouter)

    def update(self, context, virtualrouter_id, values):
        with self.transactional() as session:
            virtualrouter = self._get(context,
                                      virtualrouter_id, session=session)
            virtualrouter.update(values)
        return virtualrouter

    def binding_network(self, network, virtualrouter, session=None):
        if not session:
            session = self.get_session()
        with session.begin(subtransactions=True):
            bn = VirtualrouterNetwork()
            bn.network = network
            bn.virtualrouter = virtualrouter
            session.add(bn)
            session.flush()

    def count_all(self):
        with self.transactional() as session:
            result = session.query(Virtualrouter).filter().count()
        return result or 0

