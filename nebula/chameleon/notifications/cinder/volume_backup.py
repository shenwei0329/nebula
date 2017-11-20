# -*- coding: utf-8 -*-
import time
import oslo.messaging
from oslo.config import cfg

from nebula.chameleon import plugin
from nebula.core import context
from nebula.core.managers import managers
from nebula.core import constants

CONF = cfg.CONF


class VolumeBackupState(plugin.NotificationBase):
    event_types = [
        'snapshot.create.error',
        'snapshot.create.end',
        'snapshot.delete.end',
        'snapshot.delete.error',
    ]

    def __init__(self):
        super(VolumeBackupState, self).__init__()

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
        time.sleep(2) # 防止同步消息未及时更新UUID到数据库
        resource_id = payload['snapshot_id']
        if event_type.find("error") != -1:
            update_values = dict(
                status=constants.VOLUME_ERROR
            )
        elif event_type == 'snapshot.create.end':
            update_values = dict(
                status=constants.VOLUME_AVAILABLE
            )
        elif event_type == 'snapshot.delete.end':
            update_values = dict(
                status=constants.VOLUME_DELETED
            )

        ctx = context.get_admin_context()
        managers.volume_backups.update_by_uuid(ctx, resource_id, **update_values)
