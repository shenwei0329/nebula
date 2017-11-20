# -*- coding: utf-8 -*-
import json
import logging

from flask import jsonify

from nebula.core.models import Alert
from nebula.core.db import session as db_session
from nebula.core.views import View
from nebula.core.managers import managers
from nebula.portal.views.base import ListView
from .base import UserMixin
from nebula.portal.views.portal.systems import SystemLogsOpView

LOG = logging.getLogger(__name__)
        
class UserAlertsView(UserMixin, SystemLogsOpView):
    template_name = 'systems/user_alerts.html'
    model_class = Alert
    search_fields = {
        "resource_name": "resource_name"
    }

    def get_searched_queryset(self):
        search_fields_dict = self.get_search_fields()

        query = self.get_filtered_queryset()
        if not search_fields_dict:
            return query

        return query
    
    def get_queryset(self):
        query = super(UserAlertsView, self).get_queryset()
        return query
