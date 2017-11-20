# -*- coding: utf-8 -*-
import logging
import os

import celery.signals as celery_signals
import six
from celery import Celery
from celery._state import get_current_task
from celery.app.log import TaskFormatter
from celery.datastructures import DictAttribute
from celery.loaders.base import BaseLoader
from celery.utils.log import ColorFormatter
from oslo.config import cfg

from nebula.core import config
from nebula.openstack.common import gettextutils

__path__ = os.path.abspath(__file__)
CONF = cfg.CONF
CONF.import_group('missions', 'nebula.mission_control.options')

gettextutils.install('nebula', lazy=True)


class Loader(BaseLoader):

    def init_worker(self):
        print 'init_worker'
        config.set_defaults(args=[], prog='nebula-missions')
        config.setup_logging()
        gettextutils.install('nebula', lazy=True)

        super(Loader, self).init_worker()

    def read_configuration(self, env='CELERY_CONFIG_MODULE'):
        conf = DictAttribute(self._import_config_module(
            'nebula.mission_control.default_config'))
        # Merge user customizations
        config.set_defaults(args=[], prog='nebula-missions')
        user_cfg = dict(CONF.missions.items())
        for k, v in six.iteritems(user_cfg):
            conf[k.upper()] = v
        return conf


class AdaptableTaskFormatter(logging.Formatter):
    """若能获取到当前的celery task, 使用 ``task_fmt`` 格式化输出日志, 反之使用
    ``fmt`` 格式化输出日志
    """

    def __init__(self, fmt=None, task_fmt=None, use_color=False):
        logging.Formatter.__init__(self, fmt)
        self._formatter = ColorFormatter(fmt=fmt, use_color=use_color)
        self._task_formatter = TaskFormatter(fmt=task_fmt, use_color=use_color)

    def formatException(self, ei):
        return self._formatter.formatException(ei)

    def format(self, record):
        task = get_current_task()
        if task:
            return self._task_formatter.format(record)
        else:
            return self._formatter.format(record)


app = Celery(main='nebula.mission_control',
             loader='nebula.mission_control.app:Loader')



@celery_signals.after_setup_logger.connect
def handle_after_setup_logger(**kwargs):
    # Configure root logger
    root_logger = logging.getLogger(None)
    for handler in root_logger.handlers:
        handler.setFormatter(AdaptableTaskFormatter(
            fmt=app.conf.CELERYD_LOG_FORMAT,
            task_fmt=app.conf.CELERYD_TASK_LOG_FORMAT,
            use_color=app.conf.CELERYD_LOG_COLOR))
