# -*- coding: utf-8 -*-
import time
import oslo.messaging
from oslo.config import cfg

from nebula.chameleon import plugin
from nebula.openstack.common import log
from nebula.core import context
from nebula.core.managers import managers
from nebula.core import constants

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class VolumeState(plugin.NotificationBase):
    event_types = [
        'volume.create.error',
        'volume.create.end',
        'volume.resize.end',
        'volume.resize.error',
        'volume.delete.error',
        'volume.delete.end',
        'volume.resize.online.end',
        'volume.detach.end',
        'volume.attach.end'
    ]

    def __init__(self):
        super(VolumeState, self).__init__()

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
        LOG.info("volume notification: %s" % payload)
        time.sleep(2) # 防止同步消息未及时更新UUID到数据库
        resource_id = payload['volume_id']
        if event_type.find('error') >= 0:
            update_values = dict(
                status=constants.VOLUME_ERROR
            )
        elif event_type == 'volume.create.end':
            update_values = dict(
                status=constants.VOLUME_AVAILABLE
            )
        elif event_type == 'volume.resize.end':
            update_values = dict(
                status=constants.VOLUME_AVAILABLE
            )
        elif event_type == 'volume.detach.end':
            update_values = dict(
                status=constants.VOLUME_AVAILABLE,
                instance_id=None
            )
        elif event_type == 'volume.delete.end':
            update_values = dict(
                status=constants.VOLUME_DELETED
            )
        elif event_type == 'volume.resize.online.end':
            update_values = dict(
                status=constants.VOLUME_IN_USE
            )
        elif event_type == 'volume.attach.end':
            update_values = dict(
                status=constants.VOLUME_IN_USE
            )

        ctx = context.get_admin_context()
        managers.volumes.update_by_uuid(ctx, resource_id, **update_values)
