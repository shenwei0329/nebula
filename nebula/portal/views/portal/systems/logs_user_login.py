# -*- coding: utf-8 -*-

from nebula.core.models import UserLogin
from nebula.portal.views.base import ListView
from .base import SystemMixin


class ActiveMixin(object):
    active_module = 'logs'


class SystemLogsUserLoginView(ActiveMixin, SystemMixin, ListView):
    template_name = 'systems/system_logs_user_login.html'
    model_class = UserLogin
