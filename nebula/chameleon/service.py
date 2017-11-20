# -*- coding: utf-8 -*-

from oslo.config import cfg

from nebula.chameleon import utils
from nebula.core import config
from nebula.openstack.common import gettextutils
from nebula.openstack.common import log
from nebula.core.i18n import _

CONF = cfg.CONF
LOG = log.getLogger(__name__)

opts = [
    cfg.IntOpt('notification_workers',
               default=1,
               help='Number of workers for notification service. A single '
                    'notification agent is enabled by default.'),
]
CONF.register_opts(opts)


class WorkerException(Exception):
    """Exception for errors relating to service workers
    """


def get_workers(name):
    workers = (cfg.CONF.get or
               utils.cpu_count())
    if workers and workers < 1:
        msg = (_("%(worker_name)s value of %(workers)s is invalid, "
                 "must be greater than 0") %
               {'worker_name': '%s_workers' % name, 'workers': str(workers)})
        raise WorkerException(msg)
    return workers


def prepare_service(prog):
    gettextutils.install('nebula', lazy=True)
    gettextutils.enable_lazy()
    config.set_defaults(prog=prog)
    config.setup_logging()
