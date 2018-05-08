# -*- coding: utf-8 -*-
import os

from oslo_config import cfg

from nebula.core.constants import DEFAULT_CONFIG_FILE

CONF = cfg.CONF
PATH = os.path.dirname(os.path.abspath(__file__))


def _find_config_files(prog=None):
    env_config_file = os.environ.get

    local_config_file = os.path.join(PATH, '../../', DEFAULT_CONFIG_FILE)
    if os.path.exists(local_config_file):
        return [os.path.abspath(local_config_file)]

    # Fallback to default load order
    return cfg.find_config_files(project='nebula', prog=prog)


def set_defaults(args=None, prog=None, version=None, config_files=(),
                 verbose=True, debug=None):
    if config_files:
        config_files = [os.path.abspath(f) for f in config_files]
    else:
        config_files = _find_config_files()
    CONF(args=args,
         project='nebula',
         prog=prog,
         version=version,
         default_config_files=config_files)


def setup_logging(version=None):
    pass
