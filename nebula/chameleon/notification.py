# -*- coding: utf-8 -*-
from oslo.config import cfg

from nebula.chameleon import messaging
from nebula.openstack.common import log as logging
from nebula.openstack.common import service as os_service
from nebula.openstack.common import importutils
from nebula.core.i18n import _

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

CONF.import_group('chameleon', 'nebula.chameleon.options')


class NotificationService(os_service.Service):
    def __init__(self, threads=1000):
        super(NotificationService, self).__init__(threads)
        self.listeners = []

    def start(self):
        super(NotificationService, self).start()

        self._load_handlers()

        if not self.handlers:
            LOG.warning(_("Failed to load any notification handlers in "
                          "CONF.chameleon.notification_handlers"))

        ack_on_error = CONF.chameleon.ack_on_event_error

        endpoints = []
        targets = []

        for handler in self.handlers:
            LOG.debug(_("Event types from %(name)s: %(type)s"
                        " (ack_on_error=%(error)s)") %
                      {'name': handler.__class__.__name__,
                       'type': ', '.join(handler.event_types),
                       'error': ack_on_error})
            targets.extend(handler.get_targets(CONF))
            endpoints.append(handler)

        urls = CONF.chameleon.messaging_urls
        for url in urls:
            # NOTE: For compatibility
            if url.startswith('amqp://'):
                url = 'rabbit://' + url[7:]
            listener = messaging.get_notification_listener(
                targets, endpoints, url)
            listener.start()
            self.listeners.append(listener)

        # Add a dummy thread to have wait() working
        self.tg.add_timer(604800, lambda: None)

    def stop(self):
        for listener in self.listeners:
            listener.stop()
        self.listeners = []
        super(NotificationService, self).stop()

    def _load_handlers(self):
        """Load notification handlers, use reflection."""
        self.handlers = []

        for handler_name in CONF.chameleon.notification_handlers:
            try:
                handler = importutils.import_object(handler_name)
            except Exception as err:
                LOG.error(_("Failed to import handler %(handler_name)s: "
                            "%(err)s"),
                          {'handler_name': handler_name,
                           'err': err})
            else:
                LOG.info(_("Loaded notification handler %s"), handler_name)
                self.handlers.append(handler)
