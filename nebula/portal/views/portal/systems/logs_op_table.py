# -*- coding: utf-8  -*-
from flask import request
from nebula.core.models import Job
from nebula.portal.views.base import ListView
from .base import SystemMixin
from nebula.openstack.common import log as logging

import time,datetime

LOG = logging.getLogger(__name__)


class ActiveMixin(object):
    active_module = 'logs'


class SystemLogsOpTableView(ActiveMixin, SystemMixin, ListView):
    template_name = 'systems/system_logs_op_table.html'
    model_class = Job
    search_fields = {
        "resource_type": "resource_type",
        "state": "state",
        "created_at1": "created_at1",
        "created_at2": "created_at2"
    }

    def get_searched_queryset(self):
        search_fields_dict = self.get_search_fields()

        query = self.get_filtered_queryset()
        if not search_fields_dict:
            return query
        
        for field_name, value in search_fields_dict.items():

            if (field_name is "created_at1") and value:
                #if value is "开始日期":
                #    continue
                value = value[6:10] + value[5] + value[0:5]
                query = query.filter(self.model_class.created_at >= value)
            elif (field_name is "created_at2") and value:
                #if value is "结束日期":
                #    continue
                value = value[6:10] + value[5] + value[0:5]
                query = query.filter(self.model_class.created_at <= value)
            elif value:
                #if value is not 0:
                query = query.filter(getattr(self.model_class, field_name).
                                     like('%' + value + '%'))
            else:
                continue

        return query
