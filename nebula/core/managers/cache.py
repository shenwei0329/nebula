# -*- coding: utf-8 -*-
from oslo.config import cfg
from sqlalchemy import func, event

from nebula.core.cache import get_cache

CONF = cfg.CONF
CONF.import_group('portal', 'nebula.portal.options')


class Cache(object):

    response_callback = None

    def __init__(self, model_class):
        self._model_class = model_class

    @property
    def _client(self):
        return get_cache()

    @property
    def default_expire(self):
        return CONF.portal.DEFAULT_KEY_EXPIRE

    def tranform_response(self, value):
        return self.response_callback(value) \
            if self.response_callback is not None else \
            value

    def key(self, *args, **kwargs):
        raise NotImplementedError()

    def exists(self, *args, **kwargs):
        return self._client.exists(self.key(*args, **kwargs))

    def get(self, *args, **kwargs):
        return self.tranform_response(self._client.get(self.key(*args, **kwargs)))

    def set(self, value, *args, **kwargs):
        return self.tranform_response(
            self._client.setex(self.key(*args, **kwargs), self.default_expire, value)
        )

    def incr(self, *args, **kwargs):
        if self.exists(*args, **kwargs):
            self._client.incr(self.key(*args, **kwargs))

    def decr(self, *args, **kwargs):
        if self.exists(*args, **kwargs):
            self._client.decr(self.key(*args, **kwargs))

    def listen_events(self):
        raise NotImplementedError()


class CountCache(Cache):

    response_callback = int

    def listen_events(self):
        def _after_create(mapper, connection, target):
            self.incr()
            self.incr(user_id=target.owner_id)

        def _after_delete(mapper, connection, target):
            self.decr()
            self.decr(user_id=target.owner_id)

        event.listen(self._model_class, 'after_insert', _after_create)
        event.listen(self._model_class, 'after_delete', _after_delete)


class CountCacheMixin(object):
    """
    继承此Mixin需要提供如下属性:

    #. model_class, 对应的Model类
    #. count_cache, 对应的Cache类

    如下::

        class VirtualrouterManager(cache.CountCacheMixin, BaseManager):

            model_class = Virtualrouter
            count_cache = VirtualrouterCountCache()
    """
    def count(self, context):
        """
        或许过于追求通用, 应该每个Manager类单独实现???
        :param context:
        :return:
        """
        user_id = None if context.is_super else context.user_id
        if self.count_cache.exists(user_id=user_id):
            return self.count_cache.get(user_id=user_id)
        else:
            count = self.model_query(context, func.count(self.model_class.id)).scalar()
            self.count_cache.set(count, user_id=user_id)
            return count
