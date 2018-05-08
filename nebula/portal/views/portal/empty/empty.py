__author__ = 'shenwei'

from flask import request
from nebula.core.views import TemplateView
from nebula.portal.views.portal.systems.base import SystemSW
from nebula.portal.utils.menu import setMenus

import logging

LOG = logging.getLogger(__name__)

class EMPTYView(SystemSW,TemplateView):
    active_module = 'aggregate'
    template_name = 'empty/empty.html'

    def get_context_data(self, **kwargs):
        context = super(EMPTYView,self).get_context_data(**kwargs)
        empty_id = request.args.get("resource_id", None)
        context.update({
            "resource_id": empty_id,
        })
        context.update(setMenus())
        return context
