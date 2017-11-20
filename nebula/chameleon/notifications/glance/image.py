# -*- coding: utf-8 -*-
import oslo.messaging
from oslo.config import cfg

from nebula.chameleon import plugin
from nebula.core import context
from nebula.core.managers import managers

import logging

LOG = logging.getLogger(__name__)

CONF = cfg.CONF


class ImageState(plugin.NotificationBase):
    event_types = [
        'image.upload',
        'image.update',
        'image.delete',
    ]

    def __init__(self):
        super(ImageState, self).__init__()

    def get_targets(self, conf):
        """Return a sequence of oslo.messaging.Target defining the exchange and
        topics to be connected for this plugin.
        """
        return [
            oslo.messaging.Target(
                topic=topic,
                exchange=conf.chameleon.glance_control_exchange)
            for topic in conf.chameleon.notification_topics
        ]

    def process_notification(self, priority, ctxt, publisher_id, event_type,
                             payload, metadata):
        if event_type == 'image.delete':
            image_id = payload['id']
            update_values = dict(
                status = 'deleted'
            )
        else :
            image_id = payload['id']
            size_g = payload.get('size', 0)
            #if size_g !=0 :
            #   size_g = size_g/1024.00/1024.00/1024.00
            update_values = dict(
                status=payload.get('status', ''),
                name=payload.get('name'),
                disk_format=payload.get('disk_format'),
                container_format=payload.get('container_format'),
                size=size_g,
                is_public=payload.get('is_public', True),
                min_disk=payload.get('min_disk', 0),
                min_ram=payload.get('min_ram', 0),
                os_distro=payload.get('properties').get('os_type', 'centos')
            )
        
        ctx = context.get_admin_context()
        # Update instance attributes
        managers.images.update_by_uuid(ctx, image_id, update_values)