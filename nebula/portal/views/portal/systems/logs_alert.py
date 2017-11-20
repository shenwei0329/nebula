# -*- coding: utf-8 -*-
import json
import logging

from flask import jsonify

from nebula.portal.views.base import (
    JsonListView,
)

from nebula.core.models import Alert
from nebula.core.db import session as db_session
from nebula.core.views import View

from nebula.core.managers import managers

LOG = logging.getLogger(__name__)


class SystemLogsAlertView(JsonListView):
    
    model_class = Alert
    
    def get_context_data(self, **kwargs):
        context = super(SystemLogsAlertView, self).get_context_data(**kwargs)
        return context

    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        alerts = list()
        result = managers.alert.get_user_all(self.context, True)
        i = 0
        for item in result:
            if i < 5:
                    alerts.append(dict(
                        name=item.resource_name,
                        prioritykey=item.prioritykey,
                        priorityname=item.priorityname,
                        id=item.resource_id,
                        key2=item.key2,
                        value=item.value,
                        description=item.description,
                        time=item.time))
            i += 1
        alerts.append(dict(number=i))
        return json.dumps(alerts)

    def post(self, *args, **kwargs):
        managers.alert.make_all_read(self.context)
        return jsonify(dict(
            code=1,
            message='success'
        ))
