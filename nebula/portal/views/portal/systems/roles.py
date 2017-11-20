# -*- coding: utf-8 -*-
import logging
from flask import jsonify
from flask import abort
from nebula.core.forms.form import NebulaForm
from wtforms import TextField
from wtforms import IntegerField
from wtforms import BooleanField
from wtforms import SelectMultipleField
from wtforms import validators
from wtforms.validators import DataRequired

from nebula.core.managers import managers
from nebula.core.models import Role
from nebula.portal.views.base import ListView
from nebula.portal.views.base import DetailView
from nebula.portal.views.base import CreateView
from nebula.portal.views.base import JsonCreateView
from .base import SystemMixin


LOG = logging.getLogger(__name__)


class RoleMixin(object):
    active_module = 'role'

    @staticmethod
    def get_users_by_active():
        users = managers.users.get_all_by_active()
        users = [(str(user.id), user.username) for user in users
                 if not user.is_super and not user.deleted]
        return users

    @staticmethod
    def get_permissions():
        permissions = managers.permissions.get_all()
        permissions = [(str(item.id), item.name) for item in permissions]
        return permissions


"""
Role List View
"""


class RoleListView(SystemMixin, RoleMixin, ListView):

    template_name = 'systems/role_list.html'
    model_class = Role

    def get_context_data(self, **kwargs):
        context = super(RoleListView, self).get_context_data(**kwargs)
        context.update({
            "users": managers.users.get_all_by_active(),
            "permissions": managers.permissions.get_all(),
        })
        return context


"""
Role Detail View
"""


class RoleDetailView(SystemMixin, RoleMixin, DetailView):
    template_name = 'systems/role_detail.html'
    model_class = Role

    def get_context_data(self, **kwargs):
        context = super(RoleDetailView, self).get_context_data(**kwargs)
        context.update({
            'users': managers.roles.get_users(self.object.id),
            'permissions': managers.roles.get_permissions(self.object.id),
        })
        return context

    def delete(self, **kwargs):
        transfer = managers.roles.delete(kwargs['id'])
        return jsonify(transfer.to_dict())


"""
Create Role Form & View
"""


class RoleCreateForm(NebulaForm):
    name = TextField('name', validators=[DataRequired()])
    active = BooleanField(u'active')
    permissions = SelectMultipleField('permissions',
                                      choices=[],
                                      validators=[DataRequired()])
    users = SelectMultipleField('users', choices=[])


class RoleCreateView(SystemMixin, RoleMixin, CreateView):

    form_class = RoleCreateForm
    template_name = 'systems/_partial/role_create.html'

    def get(self, **kwargs):
        context = dict(
            users=managers.users.get_all_by_active(),
            permissions=managers.permissions.get_all(),
        )
        return self.render_template(self.template_name, **context)

    def post(self, *args, **kwargs):
        form = self.form_class()
        form.permissions.choices = self.get_permissions()
        form.users.choices = self.get_users_by_active()
        if form.users.data == [u'None']:
            form.users.data = []
        if form.validate():
            transfer = managers.roles.create(name=form.name.data,
                                             permissions=form.permissions.data,
                                             users=form.users.data)
            return jsonify(transfer.to_dict())
        return jsonify({'errors': form.errors})


"""
Role Update Permission Form & View
"""


class UpdatePermissionForm(NebulaForm):
    role_id = IntegerField('role_id', validators=[DataRequired()])
    permissions = SelectMultipleField('permissions',
                                      choices=[],
                                      validators=[DataRequired()])

    def validate_role(self, field):
        role = managers.roles.get(field.data)
        if not role:
            raise validators.ValidationError(
                message=u'The Role id no validation.')


class RoleUpdatePermissionView(SystemMixin, RoleMixin, CreateView):
    template_name = 'systems/_partial/role_update_permission.html'
    form_class = UpdatePermissionForm

    def get(self, *args, **kwargs):
        role = managers.roles.get(kwargs['id'])
        if not role:
            abort(404)
        context = {
            'role': role,
            'permissions': managers.roles.get_permissions(role.id),
        }
        return self.render_template(self.template_name, **context)

    def post(self, *args, **kwargs):
        form = self.form_class()
        form.permissions.choices = self.get_permissions()
        if form.validate():
            transfer = managers.roles.update_permissions(
                role_id=form.role_id.data,
                permissions=form.permissions.data
            )
            return jsonify(transfer.to_dict())
        return jsonify({'error': form.errors})


"""
Role Update User Form & View
"""


class UpdateUserForm(NebulaForm):
    role_id = IntegerField('role_id', validators=[DataRequired()])
    users = SelectMultipleField('users', choices=[])


class RoleUpdateUserView(SystemMixin, RoleMixin, CreateView):
    template_name = 'systems/_partial/role_update_user.html'
    form_class = UpdateUserForm

    def get(self, *args, **kwargs):
        role = managers.roles.get(kwargs['id'])
        if not role:
            abort(404)
        context = {
            'role': role,
            'users': managers.roles.get_users(role.id),
        }
        return self.render_template(self.template_name, **context)

    def post(self, *args, **kwargs):
        form = self.form_class()
        form.users.choices = self.get_users_by_active()
        if form.validate():
            transfer = managers.roles.update_users(
                role_id=form.role_id.data,
                users=form.users.data
            )
            return jsonify(transfer.to_dict())
        return jsonify({'errors': form.errors})


"""
Role Update Information Form & View
"""


class RoleUpdateForm(NebulaForm):
    role_id = IntegerField('role_id', validators=[DataRequired()])
    name = TextField('name', validators=[DataRequired()])
    switch = BooleanField("switch")

    def validate(self):
        role = managers.roles.get(self.role_id.data)
        if not role:
            raise validators.ValidationError(
                message=u'The Role not exist.'
            )
        return True


class RoleUpdateView(SystemMixin, RoleMixin, JsonCreateView):
    form_class = RoleUpdateForm

    def post(self, *args, **kwargs):
        form = self.form_class()
        if form.validate():
            transfer = managers.roles.update(role_id=form.role_id.data,
                                             name=form.name.data,
                                             active=form.switch.data)
            return jsonify(transfer.to_dict())
        return jsonify({'errors': form.errors})
