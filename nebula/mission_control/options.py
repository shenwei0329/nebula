# -*- coding: utf-8 -*-

from oslo.config import cfg

CONF = cfg.CONF

missions_opts = [
    cfg.StrOpt('BROKER_URL',
               default=None,
               help="Default broker URL"),
    cfg.StrOpt('BROKER_API',
               default=None,
               help="Default broker api URL"),
    cfg.FloatOpt('BROKER_HEARTBEAT',
                 default=60.0,
                 help="Broker heartbeat (RabbitMQ Only)"),
    cfg.FloatOpt('BROKER_HEARTBEAT_CHECKRATE',
                 default=2.0,
                 help="At intervals the worker will monitor that the broker "
                      "has not missed too many heartbeats"),
    cfg.BoolOpt('BROKER_CONNECTION_RETRY',
                default=True,
                help="Automatically try to re-establish the connection to the "
                     "AMQP broker if lost"),
    cfg.IntOpt('BROKER_CONNECTION_MAX_RETRIES',
               default=100,
               help="Maximum number of retries before we give up "
                    "re-establishing a connection to the AMQP broker"),
    cfg.IntOpt('BROKER_CONNECTION_TIMEOUT',
               default=4,
               help="The default timeout in seconds before we give up "
                    "establishing a connection to the AMQP server"),
]

CONF.register_opts(missions_opts, group='missions')
