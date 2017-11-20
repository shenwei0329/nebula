# -*- coding: utf-8 -*-
import abc
import fnmatch

import six

from nebula.openstack.common import log as logging
from nebula.core.i18n import _

LOG = logging.getLogger(__name__)


class PluginBase(object):
    """Base class for all plugins.
    """


@six.add_metaclass(abc.ABCMeta)
class NotificationBase(PluginBase):
    """Base class for plugins that support the notification API."""

    def __init__(self):
        super(NotificationBase, self).__init__()

    @abc.abstractproperty
    def event_types(self):
        """Return a sequence of strings defining the event types to be
        given to this plugin.
        """

    @abc.abstractmethod
    def get_targets(self, conf):
        """Return a sequence of oslo.messaging.Target defining the exchange and
        topics to be connected for this plugin.

        :param conf: Configuration.
        """

    @abc.abstractmethod
    def process_notification(self, priority, ctxt, publisher_id, event_type,
                             payload, metadata):
        """Process notification message

        :param ctxt: oslo.messaging context
        :param publisher_id: publisher of the notification
        :param event_type: type of notification
        :param payload: notification payload
        :param metadata: metadata about the notification
        """

    @staticmethod
    def _handle_event_type(event_type, event_type_to_handle):
        """Check whether event_type should be handled according to
        event_type_to_handle.

        """
        return any(map(lambda e: fnmatch.fnmatch(event_type, e),
                       event_type_to_handle))

    def _priority(self, priority, ctxt, publisher_id, event_type, payload,
                  metadata):
        """Base RPC endpoint for notification messages

        When another service sends a notification over the message
        bus, this method receives it.

        :param ctxt: oslo.messaging context
        :param publisher_id: publisher of the notification
        :param event_type: type of notification
        :param payload: notification payload
        :param metadata: metadata about the notification
        """
        if not self._handle_event_type(event_type, self.event_types):
            LOG.debug(_("Event %(event_type)s not in set %(event_types)s, "
                        "Skip"),
                      {
                          'event_type': event_type,
                          'event_types': self.event_types,
                      })
            return
        LOG.info(_("Processing notification, event_type=%s"), event_type)
        try:
            self.process_notification(priority, ctxt, publisher_id, event_type,
                                      payload, metadata)
        except Exception as err:
            LOG.error(_("Error occurred while processing notification"))
            LOG.exception(err)

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        self._priority('info', ctxt, publisher_id, event_type, payload,
                       metadata)

    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        self._priority('error', ctxt, publisher_id, event_type, payload,
                       metadata)


@six.add_metaclass(abc.ABCMeta)
class PollsterBase(PluginBase):
    @abc.abstractmethod
    def poll(self, manager, cache):
        """Poll once.

        :param manager: The service manager class invoking the plugin.
        :param cache: A dictionary to allow pollsters to pass data
                      between themselves when recomputing it would be
                      expensive (e.g., asking another service for a
                      list of objects).
        """
