# -*- coding: utf-8 -*-


def nebula_mission_config():
    from oslo.config import cfg
    from nebula.core import config

    CONF = cfg.CONF
    CONF.import_group('missions', 'nebula.mission_control.options')
    config.set_defaults(args=[], prog='nebula-missions')
    config.setup_logging()

    return CONF
