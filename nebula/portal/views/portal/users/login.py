# -*- coding: utf-8 -*-

from flask import request
from flask import redirect
from flask import render_template
from flask import session
from flask.views import MethodView
from nebula.core.forms.form import NebulaForm
from wtforms import PasswordField
from wtforms import TextField
from wtforms.validators import DataRequired

from nebula.portal.urlutils import redirect_url
from nebula.portal.userutils import login_user
from flask import url_for


class LoginForm(NebulaForm):
    username = TextField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])

class LoginView(MethodView):

    methods = ['GET', 'POST']

    _template_name = 'user/login.html'

    def dispatch_request(self, *args, **kwargs):
        self.next_url = redirect_url()
        if 'user' in session:
            return redirect(redirect_url())
        return super(LoginView, self).dispatch_request(*args, **kwargs)

    def get(self):
        context = dict(
            form=LoginForm(),
        )
        return render_template(self._template_name, **context)

    def post(self):
        form = LoginForm()
        if form.validate_on_submit():
            login_user(request, None)
            return redirect(url_for('portal.cdh'))
            #return redirect(url_for('portal.dashboard'))
        
        context = dict(
            form=form,
        )

        return render_template(self._template_name, **context)
