# -*- coding: utf-8 -*-

import logging

from flask import session
from flask import jsonify
from nebula.core.forms.form import NebulaForm
from wtforms import TextField, IntegerField
from wtforms import validators

from nebula.core.managers import managers
from nebula.core.i18n import _
from .base import UserBaseView

LOG = logging.getLogger(__name__)


class ProfileForm(NebulaForm):
    email = TextField('email', validators=[validators.DataRequired(), validators.email()])
    phone = IntegerField('phone', validators=[validators.optional()])


class UserProfileView(UserBaseView):

    template_name = 'user/profile.html'

    def get_context_data(self, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)
        context.update({
            "profile": managers.users.get_by_id(session['user']['id']),
            "quotas": managers.quotas.get_user_quotas_for_ui(session['user']['id']),
            'form': ProfileForm(),
        })
        return context

    def get(self, **kwargs):
        return self.render_template(self.template_name,
                                    **self.get_context_data(**kwargs))

    def post(self, **kwargs):
        form = ProfileForm()
        if form.validate():
            managers.users.update(
                user_id=session['user']['id'],
                email=form.email.data,
                phone=form.phone.data
            )
        context = self.get_context_data(**kwargs)
        context.update({'form': form})
        return self.render_template(self.template_name, **context)


"""
Rest Password Form & View
"""


class UserRestPasswordForm(NebulaForm):
    password = TextField('password',
                         validators=[
                             validators.DataRequired()])
    new_password = TextField('new_password',
                             validators=[
                                 validators.DataRequired()])
    confirm_password = TextField('confirm_password',
                                 validators=[
                                     validators.DataRequired(),
                                     validators.EqualTo('new_password',
                                                        message=u'paswords must match' )])

    def validate_password(self, field):
        user = managers.users.get_by_id(session['user']['id'])
        if not user:
            raise validators.ValidationError(
                message=_(u'not found user')
            )
        if not user.check_password(field.data):
            raise validators.ValidationError(
                message=_(u'origin password not validate')
            )


class UserRestPasswordView(UserBaseView):

    def post(self, *args, **kwargs):
        form = UserRestPasswordForm()
        if form.validate():
            managers.users.change_password(session['user']['id'],
                                           form.new_password.data)
            return jsonify({})
        return jsonify({'errors': form.errors})
