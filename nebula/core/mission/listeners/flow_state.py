# -*- coding: utf-8 -*-

from taskflow.listeners import base

from nebula.core import context
from nebula.core.managers import managers


class Listener(base.ListenerBase):
    """
    在 Flow 状态变更时, 更新 Job 表中相应的状态
    """

    def __init__(self, engine):
        super(Listener, self).__init__(
            engine,
            task_listen_for=[],  # Do not listen on the task notifier
            flow_listen_for=('*',))
        self.context = context.get_admin_context()

    def _flow_receiver(self, state, details):
        managers.jobs.update_state_by_flow_uuid(self.context,
                                                details['flow_uuid'],
                                                state)
