# -*- coding: utf-8 -*-
import redis
from oslo_config import cfg

CONF = cfg.CONF
CONF.import_group('portal', 'nebula.portal.options')


class CacheFacade(object):

    def __init__(self, host='localhost', port=6379, password=None,
                 db=0, default_timeout=300, key_prefix=None):
        super(CacheFacade, self).__init__()

        # self._cache = RedisCache(host=host, port=port, password=password,
        #                          db=db, default_timeout=default_timeout, key_prefix=key_prefix)
        self._cache = redis.StrictRedis(host=host, port=port, db=db, password=password)

    def get_cache(self):
        return self._cache

    @classmethod
    def from_config(cls, host, port, password=None, db=0,
                    default_timeout=300, key_prefix=None):
        return cls(host=host, port=port, password=password, db=db,
                   default_timeout=default_timeout, key_prefix=key_prefix)

_FACADE = None

def _create_facade_lazily():
    global _FACADE

    if _FACADE is None:
        _FACADE = CacheFacade.from_config(
            cfg.CONF.portal.REDIS_HOST, cfg.CONF.portal.REDIS_PORT,
            cfg.CONF.portal.REDIS_PASSWORD, cfg.CONF.portal.REDIS_DB)

    return _FACADE

def get_cache():
    facade = _create_facade_lazily()
    return facade.get_cache()
