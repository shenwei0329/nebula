# -*- coding: utf-8 -*-

import logging

from nebula.core.forms.form import NebulaForm
from wtforms import IntegerField
from wtforms import validators
from wtforms.validators import InputRequired

from .base import SystemMixin
from nebula.portal.views.base import AuthorizedView
from nebula.core.managers import managers

LOG = logging.getLogger(__name__)


class ResourceSettingMixin(object):
    active_module = 'resource_settings'


class ResourceSettingForm(NebulaForm):
    instance_attach_volumes = IntegerField('instance_attach_volumes',
                                           validators=[
                                               InputRequired(),
                                               validators.NumberRange(min=1,
                                                                      max=12)])
    instance_attach_ports = IntegerField('instance_attach_ports',
                                         validators=[
                                             InputRequired(),
                                             validators.NumberRange(min=1,
                                                                    max=8)])
    instance_backups = IntegerField('instance_backups',
                                    validators=[
                                        InputRequired(),
                                        validators.NumberRange(min=5, max=50)])
    instance_cores_min = IntegerField('instance_cores_min',
                                      validators=[
                                          InputRequired(),
                                          validators.NumberRange(min=1,
                                                                 max=128)])
    instance_cores_max = IntegerField('instance_cores_max',
                                      validators=[
                                          InputRequired(),
                                          validators.NumberRange(min=1,
                                                                 max=128)])
    instance_ram_min = IntegerField('instance_ram_min',
                                    validators=[
                                        InputRequired(),
                                        validators.NumberRange(min=1024,
                                                               max=16 * 1024)])
    instance_ram_max = IntegerField('instance_ram_max',
                                    validators=[
                                        InputRequired(),
                                        validators.NumberRange(min=1024,
                                                               max=16 * 1024)])
    instance_batches = IntegerField('instance_batches',
                                    validators=[
                                        InputRequired(),
                                        validators.NumberRange(min=1, max=1000)])
    volume_backups = IntegerField('volume_backups',
                                  default=1,
                                  validators=[InputRequired(),
                                              validators.NumberRange(min=1,
                                                                     max=50)])
    volume_capacity = IntegerField('volume_capacity',
                                   validators=[
                                       InputRequired(),
                                       validators.NumberRange(min=1, max=2048)])
    network_vlan_min = IntegerField('network_vlan_min',
                                    validators=[InputRequired(),
                                                validators.NumberRange(min=2,
                                                                       max=4093)])
    network_vlan_max = IntegerField('network_vlan_max',
                                    validators=[InputRequired(),
                                                validators.NumberRange(min=2,
                                                                       max=4093)])

    def validate_instance_ram_max(self, field):
        if field.data <= self.instance_ram_min.data:
            raise validators.ValidationError(
                message=u'Ram max value must greater than min value.')

    def validate_instance_cores_max(self, field):
        if field.data <= self.instance_cores_min.data:
            raise validators.ValidationError(
                message=u'Cores max value must greater than min value')

    def validate_network_vlan_max(self, field):
        if field.data <= self.network_vlan_min.data:
            raise validators.ValidationError(
                message=u"Network's vlan max value must greater than min value"
            )

    def to_dict(self):
        data = {}
        for name, field in self._fields.iteritems():
            if name == 'csrf_token':
                continue
            data.update({
                name: field.data
            })
        LOG.error(data)
        return data


class ResourceSettingView(SystemMixin, ResourceSettingMixin, AuthorizedView):
    template_name = 'systems/resource_settings.html'

    def get_context_data(self, **kwargs):
        context = super(ResourceSettingView, self).get_context_data(**kwargs)
        context.update(dict(
            settings=managers.settings.get_settings(),
        ))
        return context

    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update(dict(form=ResourceSettingForm()))
        return self.render_template(self.template_name, **context)

    def post(self, *args, **kwargs):
        form = ResourceSettingForm()
        context = self.get_context_data(**kwargs)
        context.update(dict(
            form=form
        ))
        if form.validate():
            kwargs = form.to_dict()
            managers.settings.create_update_setting(**kwargs)
            context.update(dict(
                settings=managers.settings.get_settings(),
            ))
            return self.render_template(self.template_name, **context)
        return self.render_template(self.template_name, **context)
