import oslo.messaging

from nebula.chameleon import plugin


class Debug(plugin.NotificationBase):
    event_types = ['*']

    def __init__(self):
        super(Debug, self).__init__()

    def get_targets(self, conf):
        """Return a sequence of oslo.messaging.Target defining the exchange and
        topics to be connected for this plugin.
        """
        return [
            oslo.messaging.Target(
                topic=topic,
                exchange=conf.chameleon.cinder_control_exchange)
            for topic in conf.chameleon.notification_topics
        ]

    def process_notification(self, priority, ctxt, publisher_id, event_type,
                             payload, metadata):
        print 'Debug notification:', payload