# -*- coding: utf-8 -*-
import logging

from flask import jsonify
from flask import flash
from nebula.core.forms.form import NebulaForm
from wtforms import TextField
from wtforms import PasswordField
from wtforms import BooleanField
from wtforms import SelectMultipleField
from wtforms import IntegerField
from wtforms import validators
from wtforms.validators import input_required

from nebula.core.i18n import _
from nebula.portal.views.base import ListView
from nebula.portal.views.base import DetailView
from nebula.portal.views.base import JsonCreateView
from .base import SystemMixin
from oslo.config import cfg

CONF = cfg.CONF
CONF.import_group('portal', 'nebula.portal.options')
LOG = logging.getLogger(__name__)


class UserMixin(object):

    active_module = 'user'

    @staticmethod
    def get_role_item():
        roles = managers.roles.get_all_by_active()
        roles = [(str(item.id), item.name) for item in roles]
        return roles


"""
User Create Form & View
"""


class UserCreateForm(NebulaForm):

    username = TextField('username', validators=[input_required()])
    email = TextField('email', validators=[input_required(),
                                           validators.Email()])
    phone = TextField('phone', validators=[validators.optional()])
    password = PasswordField('password', validators=[input_required()])
    roles = SelectMultipleField('roles', choices=[], validators=[])
    # active = BooleanField(u'active')
    instances = IntegerField('instances', validators=[input_required()])
    cores = IntegerField('cores', validators=[input_required()])
    ram = IntegerField('ram', validators=[input_required()])
    volumes = IntegerField('volumes', validators=[input_required()])
    private_networks = IntegerField('private_networks',
                                    validators=[input_required()])
    virtual_routers = IntegerField('virtual_routers',
                                   validators=[input_required()])
    images = IntegerField('images', validators=[input_required()])
    bandwidth_tx = IntegerField(u'bandwidth_tx', validators=[input_required()])
    bandwidth_rx = IntegerField(u'bandwidth_rx', validators=[input_required()])
    firewalls = IntegerField(u'firewalls', validators=[input_required()])
    region = TextField(u'区域', validators=[input_required()],
                       default=CONF.portal.REGION_NAME)

    @property
    def quotas(self):
        return dict(
            instances=self.instances.data,
            cores=self.cores.data,
            ram=self.ram.data,
            volumes=self.volumes.data,
            virtual_routers=self.virtual_routers.data,
            private_networks=self.private_networks.data,
            images=self.images.data,
            bandwidth_tx=self.bandwidth_tx.data,
            bandwidth_rx=self.bandwidth_rx.data,
            firewalls=self.firewalls.data,
        )


class UserCreateView(SystemMixin, UserMixin, JsonCreateView):

    form_class = UserCreateForm
    template_name = 'systems/_partial/user_create.html'

    def get_context_data(self, **kwargs):
        context = dict(
            roles=managers.roles.get_all_by_active(),
            quotas=quota.QUOTAS.get_defaults(self.context),
        )
        return context

    def get(self, *args, **kwargs):

        return self.render_template(self.template_name,
                                    **self.get_context_data(**kwargs))

    def post(self, *args, **kwargs):
        form = self.form_class()
        form.roles.choices = self.get_role_item()
        if form.roles.data == [u'None']:
            form.roles.data = []
        if form.validate():
            transfer = managers.users.new(username=form.username.data,
                                          password=form.password.data,
                                          phone=form.phone.data,
                                          email=form.email.data,
                                          # active=form.active.data,
                                          roles=form.roles.data,
                                          quotas=form.quotas,
                                          region=form.region.data)
            if transfer.state:
                flash(transfer.message)
            return jsonify(transfer.to_dict())
        return jsonify({'errors': form.errors})


"""
Set User' role Form & View
"""


class UserRoleForm(NebulaForm):

    user_id = TextField('user_id', validators=[input_required()])
    roles = SelectMultipleField('roles', choices=[])


class UserSetRoleView(SystemMixin, UserMixin, JsonCreateView):
    """
    Set User Role View
    """
    form_class = UserRoleForm

    def post(self, *args, **kwargs):
        form = self.form_class()
        form.roles.choices = self.get_role_item()
        if form.validate():
            LOG.info("set user's role form  validate")
            LOG.info(form.roles.choices)
            LOG.info(form.roles.data)
            transfer = managers.users.set_roles(user_id=form.user_id.data,
                                                roles=form.roles.data)
            return jsonify(transfer.to_dict())
        return jsonify({'errors': form.errors})


"""
Reset User's Password Form & View
"""


class ResetPasswordForm(NebulaForm):
    user_id = TextField('user_id', validators=[input_required()])
    password = PasswordField('password', validators=[input_required()])
    confirm_password = PasswordField('confirm_password',
                                     validators=[input_required()])

    def validate(self):
        super(ResetPasswordForm, self).validate()
        if self.password.data != self.confirm_password.data:
            raise ValueError(_("password and confirm password are different."))
        return True


class UserResetPasswordView(SystemMixin, UserMixin, JsonCreateView):
    """
    Reset user's password view.
    """
    form_class = ResetPasswordForm

    def post(self, *args, **kwargs):
        form = self.form_class()
        if form.validate():
            managers.users.change_password(form.user_id.data,
                                           form.password.data)
            return jsonify({'errors': {}})
        return jsonify({"errors": form.errors})


"""
Update User's Profile Form and View
"""


class UserUpdateForm(NebulaForm):
    user_id = TextField(_(u'user_id'), validators=[input_required()])
    username = TextField(_(u'username'), validators=[input_required()])
    email = TextField(_(u'email'))
    phone = TextField(_(u'phone'))
    status = BooleanField(_(u'status'))

    # def validate_username(self, field):
    #     exists_name = managers.users.find_duplicate_username(self.user_id.data,
    #                                                          field.data)
    #     if exists_name:
    #         raise validators.ValidationError(
    #             message=u'Duplicate Name, can not set.'
    #         )
    #     return True

    def quotas(self):
        return dict(
        )


class UserUpdateView(SystemMixin, UserMixin, JsonCreateView):
    form_class = UserUpdateForm

    def post(self, *args, **kwargs):
        form = self.form_class()
        if form.validate():
            transfer = managers.users.update(
                user_id=form.user_id.data,
                username=form.username.data,
                email=form.email.data,
                phone=form.phone.data,
                status=form.status.data,
            )
            managers.quotas.update_quotas(user_id=form.user_id.data,
                                          resources=form.quotas())
            return jsonify(transfer.to_dict())
        return jsonify({'errors': form.errors})


"""
Update User's Status Form & View
"""


class UserStatusForm(NebulaForm):
    user_id = TextField('user_id', validators=[input_required()])
    switch = BooleanField('switch')


class UserStatusView(SystemMixin, UserMixin, JsonCreateView):
    form_class = UserStatusForm

    def post(self, *args, **kwargs):
        form = self.form_class()
        if form.validate():
            result = managers.users.update_status(
                user_id=form.user_id.data,
                status=form.switch.data
            )
            ret_data = dict(
                errors=None
            )
            if not result:
                ret_data.update({
                    'errors': {
                        'result': u'Update user status failure.'
                    }
                })
            return jsonify(ret_data)
        return jsonify({'errors': form.errors})
