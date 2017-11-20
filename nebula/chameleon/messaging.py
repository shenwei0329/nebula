# -*- coding: utf-8 -*-
import oslo.messaging
from oslo.config import cfg

TRANSPORT = None
CONF = cfg.CONF

_ALIASES = {
    'amqp': 'rabbit',
}


def get_notification_listener(targets, endpoints, url):
    """Return a configured oslo.messaging notification listener."""
    transport = oslo.messaging.get_transport(CONF, url,
                                             aliases=_ALIASES)

    return oslo.messaging.get_notification_listener(
        transport, targets, endpoints, executor='eventlet')
