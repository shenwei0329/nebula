# -*- coding: utf-8 -*-
from flask import redirect
from flask import url_for
from flask.views import MethodView

from nebula.portal.decorators.auth import require_auth

class HomeView(MethodView):

    decorators = (require_auth, )

    def get(self):
        return redirect(url_for('portal.cdh'))
