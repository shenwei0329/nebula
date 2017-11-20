# -*- coding: utf-8 -*-

from kombu import Exchange
from kombu import Queue

CELERY_ACCEPT_CONTENT = ['json']

CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'Asia/Shanghai'

## Result backend setting
# Use amqp as backend
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'amqp'
CELERY_RESULT_EXCHANGE = 'nebula.mission_control.results'
CELERY_RESULT_EXCHANGE_TYPE = 'direct'
CELERY_RESULT_PERSISTENT = False
CELERY_TASK_RESULT_EXPIRES = 3600 * 1  # 1 hour

## Worker
# Tasks
CELERY_TASK_SERIALIZER = 'json'
CELERY_IMPORTS = ('nebula.mission_control.tasks', )

## Default Queue Configuration
# The mapping of queues the worker consumes from.
CELERY_CREATE_MISSING_QUEUES = False

CELERY_DEFAULT_QUEUE = 'nebula.mission_control.default'
CELERY_DEFAULT_EXCHANGE = 'nebula.mission_control.default'
CELERY_DEFAULT_EXCHANGE_TYPE = 'direct'

CELERY_QUEUES = (
    Queue(CELERY_DEFAULT_QUEUE,
          Exchange(CELERY_DEFAULT_EXCHANGE),
          routing_key='default'),
    Queue('nebula.mission_control.flows',
          Exchange('nebula.mission_control.flows'),
          routing_key='flows'),
)

CELERY_ROUTES = {
    'nebula.mission_control.tasks.flows.execute_job': {
        'queue': 'nebula.mission_control.flows',
        'routing_key': 'flows',
    },
}

## Message Settings
CELERY_MESSAGE_COMPRESSION = None

## Periodic Task config
CELERYBEAT_SCHEDULE = {
}

CELERYD_HIJACK_ROOT_LOGGER = True
