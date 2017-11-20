# -*- coding: utf-8 -*-
from flask import redirect
from flask import url_for
from flask.views import MethodView


class HomeView(MethodView):

    def get(self):
        return redirect(url_for('portal.cdh'))
