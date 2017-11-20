# -*- coding: utf-8 -*-

from flask import redirect
from flask import url_for
from nebula.core.models import Alert
from nebula.portal.views.base import ListView
from .base import SystemMixin


class ActiveMixin(object):
    active_module = 'logs'


class SystemLogsView(ActiveMixin, SystemMixin, ListView):
    template_name = 'systems/system_logs.html'
    model_class = Alert

    def get(self, *args, **kwargs):
        return redirect(url_for('portal.system_logs_warning'))
