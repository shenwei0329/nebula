# -*- coding: utf-8 -*-

import logging
from nebula.core.models import Meters
from nebula.core.managers import managers

from nebula.core.i18n import _

from nebula.core.forms.form import NebulaForm

from nebula.portal.views.base import ListView
from nebula.portal.views.base import JsonCreateView

from .base import SystemMixin
from flask import jsonify
from wtforms import (
    validators,
    IntegerField
)

LOG = logging.getLogger(__name__)

class MetersMixin(object):
    active_module = 'alarm_meters'

class AlarmMetersView(MetersMixin,SystemMixin, ListView):
    template_name = 'systems/meters.html'
    model_class = Meters

class UpdateAlarmMeterDataForm(NebulaForm):
    stat = IntegerField(u'stat', validators=[
                                       validators.InputRequired(),
                                       validators.number_range(min=0, max=1)])
    id = IntegerField(u'id', validators=[])


class UpdateAlarmMeterDataView(MetersMixin, SystemMixin, JsonCreateView):
    form_class = UpdateAlarmMeterDataForm

    def post(self, *args, **kwargs):
        form = self.form_class()
        stat = form.stat.data
        meter_id = form.id.data
        if form.validate():
            # update alarm meter data
            result = managers.alarm_meters.update( self.context,
                                                   meter_id,
                                                   dict(state=stat))
            ret_data = dict(
            )
            if not result:
                ret_data.update({
                    'errors': _(u'Update alarm meter status failure.')
                })
            return jsonify(ret_data)
        return jsonify({'errors': form.errors})