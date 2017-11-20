# -*- coding: utf-8 -*-

import logging
from .base import UserMixin
from nebula.portal.views.portal.systems import SystemLogsOpView

LOG = logging.getLogger(__name__)


# class UserLogView(UserMixin, ListView):
#     template_name = 'user/log.html'
#     model_class = Job
#     filter_fields = {
#         'owner_id': 'owner_id'
#     }


class UserLogView(UserMixin, SystemLogsOpView):

    user_only = True

    def get_context_data(self, **kwargs):
        context = super(UserLogView, self).get_context_data(**kwargs)
        context.update({
            'user_log': True
        })
        return context
