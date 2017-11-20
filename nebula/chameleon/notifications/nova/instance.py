# -*- coding: utf-8 -*-
import logging

import oslo.messaging
from oslo.config import cfg

from nebula.chameleon import plugin
from nebula.core import context
from nebula.core.managers import managers
from nebula.core.mission.flows.hosts.host_sync import HostSyncBuilder

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class InstanceState(plugin.NotificationBase):
    event_types = [
        'compute.instance.update',
        'compute.instance.delete.end',
        'compute.instance.resize.start',
        'compute.instance.resize.end',
        'compute.instance.reboot.end',
        'compute.instance.pause.end',
        'compute.instance.unpause.end',
        'compute.instance.power_off.end',
        'compute.instance.suspend',
    ]

    def __init__(self):
        super(InstanceState, self).__init__()

    def get_targets(self, conf):
        """Return a sequence of oslo.messaging.Target defining the exchange and
        topics to be connected for this plugin.
        """
        return [
            oslo.messaging.Target(
                topic=topic,
                exchange=conf.chameleon.nova_control_exchange)
            for topic in conf.chameleon.notification_topics
        ]

    def process_notification(self, priority, ctxt, publisher_id, event_type,
                             payload, metadata):
        resource_id = payload['instance_id']
        if event_type == 'compute.instance.delete.end':
            # Mark instance state as `deleted'
            update_values = dict(
                vm_state='deleted',
                task_state=None,
            )
        else:
            update_values = dict(
                vm_state=payload['state'],
                task_state=payload.get('new_task_state'),
            )

        ctx = context.get_admin_context()
        # Update instance attributes
        managers.instances.update_by_uuid(ctx, resource_id, update_values)


class InstanceCreateEnd(plugin.NotificationBase):
    event_types = [
        'compute.instance.create.end',
    ]

    def __init__(self):
        super(InstanceCreateEnd, self).__init__()

    def get_targets(self, conf):
        """Return a sequence of oslo.messaging.Target defining the exchange and
        topics to be connected for this plugin.
        """
        return [
            oslo.messaging.Target(
                topic=topic,
                exchange=conf.chameleon.nova_control_exchange)
            for topic in conf.chameleon.notification_topics
        ]

    def process_notification(self, priority, ctxt, publisher_id, event_type,
                             payload, metadata):
        ctx = context.get_admin_context()
        #LOG.info("payload: %s ---------------------------<<<", payload)
        resource_id = payload['instance_id']
        host = payload['host']
        update_values = dict(availability_zone=payload['availability_zone'],
                             vm_state=payload['state'])
        compute_node_ref = managers.compute_nodes.get_by_hostname(ctx, host)

        if host and compute_node_ref:
            update_values.update(dict(compute_node_id=compute_node_ref.id))

        # Update instance attributes
        managers.instances.update_by_uuid(ctx, resource_id, update_values)
        try:
            builder = HostSyncBuilder(context.get_admin_context(), resource_kwargs={})
            builder.build()
        except Exception as e:
            LOG.error("HostSync")
            LOG.error(e)





class InstanceBackupState(plugin.NotificationBase):
    event_types = [
        'compute.instance.backup2.start',
        'compute.instance.backup2.end',
        'compute.instance.backup2_delete.end',
        'compute.instance.live_migration._post.end',
        'compute.instance.live_migration._rollback.end'
    ]

    def __init__(self):
        super(InstanceBackupState, self).__init__()

    def get_targets(self, conf):
        """Return a sequence of oslo.messaging.Target defining the exchange and
        topics to be connected for this plugin.
        """
        return [
            oslo.messaging.Target(
                topic=topic,
                exchange=conf.chameleon.nova_control_exchange)
            for topic in conf.chameleon.notification_topics
        ]


    def process_notification(self, priority, ctxt, publisher_id, event_type,
                             payload, metadata):
        if event_type == 'compute.instance.backup2.start':
            instance_uuid = payload['instance_id']
            update_values = dict(
                vm_state = "backup_disk",  
                task_state = "backuping"  
            )
            ctx = context.get_admin_context()
            managers.instances.update_by_uuid(ctx, instance_uuid, update_values)
            
        elif event_type == 'compute.instance.backup2.end':
            backup_uuid = payload['backup_uuid']
            update_values = dict(
                status=payload['state']    
            )
            ctx = context.get_admin_context()
            # Update instance_backups attributes
            managers.instance_backups.update_by_backup_uuid(ctx, backup_uuid, update_values)    
        elif event_type == 'compute.instance.backup2_delete.end':
            backup_uuid = payload['backup_uuid']
            ctx = context.get_admin_context()
            # Update instance_backups attributes
            managers.instance_backups.delete_by_uuid(ctx, backup_uuid)
        else:
            instance_uuid = payload['instance_id']
            update_values = dict(
                vm_state=payload['state'],
                task_state = None
            )
            ctx = context.get_admin_context()
            # Update instance_backups attributes
            managers.instances.update_by_uuid(ctx, instance_uuid, update_values)
