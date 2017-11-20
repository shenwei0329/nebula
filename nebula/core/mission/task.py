# -*- coding: utf-8 -*-
from taskflow import task
from taskflow.utils import misc

from nebula.core import context
from nebula.core.managers import managers
from nebula.openstack.common import log as logging
from nebula.core.i18n import _


LOG = logging.getLogger(__name__)


class NebulaTask(task.Task):

    def __init__(self, name=None, provides=None, requires=None,
                 auto_extract=True, rebind=None, addons=None):
        task_requires = set(['resource_id', 'job_id', 'logger',
                             '_request_context'])
        if requires:
            task_requires.union(set(task_requires))

        super(NebulaTask, self).__init__(
            name=name or self._make_task_name(self.__class__, addons),
            provides=provides,
            requires=task_requires,
            auto_extract=auto_extract,
            rebind=rebind)
        self.admin_context = context.get_admin_context()

    @staticmethod
    def _make_task_name(cls, addons=None):
        """Makes a pretty name for a task class."""
        base_name = ".".join([cls.__module__, cls.__name__])
        extra = ''
        if addons:
            extra = ';%s' % (", ".join([unicode(a) for a in addons]))
        return base_name + extra

    def update_job_state_desc(self, job_id, state_desc):
        managers.jobs.update(self.admin_context, job_id,
                             {'state_desc': state_desc})

    @classmethod
    def get_request_context(cls, **kwargs):
        request_context = context.RequestContext.from_dict(
            kwargs['_request_context'])
        return request_context

    @classmethod
    def get_logger(cls, **kwargs):
        logger = kwargs['logger']
        return logger

    @classmethod
    def log_current_task_failures(cls, *args, **kwargs):
        result = kwargs['result']
        if cls.is_current_task_failed(result):
            logger = cls.get_logger(**kwargs)
            logger.error(
                _("Current atom/task execution failed: %(exception_str)s\n"
                  "Context: args=%(args)s, kwargs=%(kwargs)s\n"
                  "traceback: %(traceback_str)s"),
                {
                    'args': args,
                    'kwargs': kwargs,
                    'exception_str': result.exception_str,
                    'traceback_str': result.traceback_str,
                })

    @classmethod
    def is_current_task_failed(cls, result):
        return not cls.is_current_task_ok(result)

    @classmethod
    def is_current_task_ok(cls, result):
        return not isinstance(result, misc.Failure)
