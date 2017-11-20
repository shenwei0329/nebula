# -*- coding: utf-8 -*-

import logging

from .base import UserBaseView

LOG = logging.getLogger(__name__)


class UserMessageView(UserBaseView):
    template_name = 'user/message.html'

    def get(self):
        return self.render_template(self.template_name, **{})