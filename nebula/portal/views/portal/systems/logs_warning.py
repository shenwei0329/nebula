# -*- coding: utf-8 -*-

from nebula.core.models import Alert
from nebula.portal.views.base import ListView

from .base import SystemMixin


class ActiveMixin(object):
    active_module = 'logs'


class SystemLogsWarningView(SystemMixin, ActiveMixin,ListView):

    template_name = 'systems/system_logs_warning.html'
    model_class = Alert