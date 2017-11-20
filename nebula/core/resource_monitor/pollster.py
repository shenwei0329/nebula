# -*- coding: utf-8 -*-
import threading
import logging
import time
from weakref import WeakSet

from nebula.core.common.lockutils import RWLock

LOG = logging.getLogger(__name__)


DEFAULT_POLLING_INTERVAL = 2.0


class GrandGenericPollster(threading.Thread):
    def __init__(self):
        super(GrandGenericPollster, self).__init__(name='GrandGenericPollster')
        self._lock = RWLock()
        self._registry = set() # WeakSet()
        self._unregistry = set()
        self._running = True
        self._polling_interval = DEFAULT_POLLING_INTERVAL
        self.daemon = True

    def register_monitor(self, monitor):
        with self._lock.writelock:
            self._registry.add(monitor)

    def unregister_monitor(self, monitor):
        with self._lock.writelock:
            LOG.info('* Removing monitor: %s', monitor)
            self._unregistry.add(monitor)

    def run(self):
        while self._running:
            try:
                self._run()
                time.sleep(self._polling_interval)
            except Exception as ex:
                LOG.exception(ex)

    def stop(self):
        self._running = False

    def _run(self):
        with self._lock.readlock:
            for monitor in self._registry:
                try:
                    LOG.info('* Polling monitor: %s', monitor)
                    monitor.poll()
                except Exception as ex:
                    LOG.exception(ex)

            # LOG.info('* Unregistry: %s', self._unregistry)
            # LOG.info('* Cleaning registry: %s', self._registry)
            self._registry.difference_update(self._unregistry)
            self._unregistry.clear()
            # LOG.info('* After clean registry: %s', self._registry)


GRAND_POLLSTER = GrandGenericPollster()
