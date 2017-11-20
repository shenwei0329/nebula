# -*- coding: utf-8 -*-
import six
from oslo.config import cfg

from nebula.core import context
from nebula.core.common import reflection
from nebula.openstack.common import log as logging
from nebula.openstack.common import service as os_service
from nebula.openstack.common import importutils
from nebula.core.i18n import _

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
CONF.import_group('chameleon', 'nebula.chameleon.options')
CONF.import_group('database', 'nebula.core.db.options')


class PollingTask(object):
    """Polling task for polling resources.
    A polling task can be invoked periodically or only once.
    """

    def __init__(self, agent_manager):
        self.manager = agent_manager
        self.pollsters = set()

    def add(self, pollster):
        self.pollsters.add(pollster)

    def poll_once(self):
        """Polling resources."""
        cache = {}
        for pollster in self.pollsters:
            name = reflection.get_fullname_of_class(pollster.__class__)
            LOG.info(_("Polling pollster %s"), name)
            try:
                pollster.poll(self.manager, cache)
            except Exception as err:
                LOG.warning(_("Continue after error from %(name)s: %(error)s")
                            % {'name': name,
                               'error': err},
                            exc_info=True)


class AgentManager(os_service.Service):

    def __init__(self, pollster_cfg_key, interval_cfg_key):
        super(AgentManager, self).__init__()
        self.pollsters = self._extensions(pollster_cfg_key)
        self.pollster_intervals = self._pollster_intervals(interval_cfg_key)
        self.context = context.get_admin_context()

    @staticmethod
    def _extensions(cfg_key):
        extensions = []
        for ext_name in CONF.chameleon[cfg_key]:
            try:
                ext = importutils.import_object(ext_name)
            except Exception as err:
                LOG.error(_("Failed to import extension %(extension_name)s: "
                            "%(error)s"),
                          {'extension_name': ext_name,
                           'error': err})
            else:
                LOG.info(_("Loaded plugin %s"), ext_name)
                extensions.append(ext)
        return extensions

    @staticmethod
    def _pollster_intervals(cfg_key):
        return dict(((k, int(v))
                     for k, v in six.iteritems(CONF.chameleon[cfg_key])))

    def create_polling_task(self):
        """Create an initially empty polling task."""
        return PollingTask(self)

    def setup_polling_tasks(self):
        polling_tasks = {}
        default_interval = CONF.chameleon.polling_interval

        for pollster in self.pollsters:
            pollster_name = reflection.get_fullname_of_class(pollster.__class__)
            interval = self.pollster_intervals.get(pollster_name,
                                                   default_interval)
            polling_task = polling_tasks.get(interval)
            if not polling_task:
                polling_task = self.create_polling_task()
                polling_tasks[interval] = polling_task
            polling_task.add(pollster)
        return polling_tasks

    def start(self):
        polling_tasks = self.setup_polling_tasks()
        if not polling_tasks:
            LOG.warning(_("No pollsters found in this agent"))
        for interval, task in six.iteritems(polling_tasks):
            self.tg.add_timer(interval, self.interval_task, task=task)

    @staticmethod
    def interval_task(task):
        task.poll_once()
