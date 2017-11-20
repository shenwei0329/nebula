# -*- coding: utf-8 -*-

from flask import redirect

import logging
from nebula.portal.urlutils import redirect_url
from nebula.portal.userutils import logout_user
from nebula.portal.views.base import AuthorizedView
from nebula.portal.decorators.auth import require_auth

LOG = logging.getLogger(__name__)


class LogoutView(AuthorizedView):

    decorators = (require_auth, )

    methods = ["GET", "POST"]

    def dispatch_request(self, *args, **kwargs):
        logout_user()
        return redirect(redirect_url())
