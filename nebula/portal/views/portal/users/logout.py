# -*- coding: utf-8 -*-

from flask import redirect

import logging
from nebula.portal.urlutils import redirect_url
from nebula.portal.userutils import logout_user
from nebula.portal.views.base import AuthorizedView
from nebula.portal.decorators.auth import require_auth
from flask import url_for

LOG = logging.getLogger(__name__)
FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT)


class LogoutView(AuthorizedView):

    decorators = (require_auth, )

    methods = ["GET", "POST"]

    def dispatch_request(self, *args, **kwargs):
        logging.warn('>>> shenwei: dispatch_request <<<')
        logout_user()
        return redirect(url_for('portal.login'))
