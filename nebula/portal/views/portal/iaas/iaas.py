#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import request
from nebula.core.views import TemplateView
from nebula.portal.views.portal.systems.base import SystemSW

import logging

LOG = logging.getLogger(__name__)

###############################################################################
# Forms
###############################################################################

class IaaSListView(SystemSW,TemplateView):
    active_module = 'aggregate'
    template_name = 'iaas/iaas.html'

    def get_context_data(self, **kwargs):
        context = super(IaaSListView,self).get_context_data(**kwargs)
        iaas_id = request.args.get("resource_id", None)
        context.update({
            "resource_id": iaas_id,
        })
        return context

