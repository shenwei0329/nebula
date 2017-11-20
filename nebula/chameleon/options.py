# -*- coding: utf-8 -*-
from oslo.config import cfg

CONF = cfg.CONF

opts = [
    cfg.BoolOpt('ack_on_event_error',
                default=True,
                deprecated_group='collector',
                help='Acknowledge message when event persistence fails.'),
    cfg.MultiStrOpt('messaging_urls',
                    default=['amqp://guest:openstack@localhost:5672//'],
                    help="Messaging URLs to listen for notifications. "
                         "Example: transport://user:pass@host1:port"
                         "[,hostN:portN]/virtual_host "
                         "(DEFAULT/transport_url is used if empty)"),
    cfg.MultiStrOpt(
        'notification_handlers',
        default=[
            'nebula.chameleon.notifications.nova.instance.InstanceState',
            'nebula.chameleon.notifications.nova.instance.InstanceCreateEnd',
            'nebula.chameleon.notifications.cinder.volume.VolumeState',
            'nebula.chameleon.notifications.cinder.volume_backup.VolumeBackupState',
            'nebula.chameleon.notifications.glance.image.ImageState',
            'nebula.chameleon.notifications.Debug',
            'nebula.chameleon.notifications.nova.instance.InstanceBackupState',
        ],
        help="A list of fully qualified name of handlers for notification "
             "agent"),

    cfg.ListOpt('notification_topics',
                default=['nova_notifications', 'cinder_notifications', 'glance_notifications'],
                help='AMQP topic used for OpenStack notifications.'),

    cfg.StrOpt('nova_control_exchange',
               default='nova',
               help="Exchange name for Nova notifications."),

    cfg.StrOpt('cinder_control_exchange',
               default='cinder',
               help="Exchange name for Cinder notifications."),
    
     cfg.StrOpt('glance_control_exchange',
               default='glance',
               help="Exchange name for Glance notifications."),

    cfg.MultiStrOpt(
        'central_pollsters',
        default=[
            'nebula.chameleon.central.pollsters.image.ImageStatus',
            'nebula.chameleon.central.pollsters.image.ImageSync',
            'nebula.chameleon.central.pollsters.instance.InstanceStatus',
        ],
        help="A list of fully qualified name of pollsters for central agent"),

    cfg.DictOpt(
        'central_pollster_intervals',
        default={
            'nebula.chameleon.central.pollsters.image.ImageStatus': 60 * 5,
            'nebula.chameleon.central.pollsters.instance.InstanceStatus': 60 * 5,
        },
        help="A mapping of fully qualified name of pollster to its interval"
             "for central agent"),

    cfg.FloatOpt(
        'polling_interval',
        help='Default polling interval, in seconds',
        default=30.0),
]
CONF.register_opts(opts, group='chameleon')
