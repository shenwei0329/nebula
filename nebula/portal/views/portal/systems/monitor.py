# -*- coding: utf-8 -*-
from flask import session
from wtforms import IntegerField
from nebula.core.openstack_clients import cml

from .base import SystemMixin
from nebula.portal.views.base import FormView
from nebula.core.forms.form import NebulaForm
from nebula.portal.views.portal.mixin import MonitorActiveMixin
from flask import jsonify

from nebula.portal.views.base import AuthorizedView

from wtforms import (
    StringField,
    validators,
)

import logging

LOG = logging.getLogger(__name__)


class MonitorManagementForm(NebulaForm):
    pass


class MonitorManagementView(MonitorActiveMixin, SystemMixin, FormView):
    template_name = 'systems/system_monitor_management.html'
    form_class = MonitorManagementForm

    def get_context_data(self, **kwargs):
        context = super(MonitorManagementView, self).get_context_data(**kwargs)
        cml_client = cml.get_client()
        values = cml_client.get_monitor_template("/template")
        LOG.info(values)
        LOG.info("values_tactic_2:::")
        
        tactic = cml_client.get_monitor_tactic('0','','')
        if 'data' in tactic:
            values_tactic = tactic['data']
            #暂时删除agent_check
            if values_tactic:
                del values_tactic[0]
                del values_tactic[len(values_tactic)-1]
            
        host_data = {}
        vm_data = {}
        if values['data']:
            for item in values["data"]:
                if item['type'] == 'HOST':
                    host_data = item
                else:
                    vm_data = item
                
        context.update({
            'main_menus': self.main_menus,
            'system_menus': self.system_menus,
            'main_menus_mini': self.main_menus_mini,
            'show_profile': self.show_profile,
            'user': session['user'],
            'monitor_host_data': host_data,
            'monitor_vm_data': vm_data,
            'monitor_tartic': values_tactic
        })
        LOG.info(values_tactic)
        return context

    def get(self, *args, **kwargs):
        return self.render_template(self.template_name,
                                    **self.get_context_data(**kwargs))


class UpdateMonitorDataForm(NebulaForm):
    host_collect_rate = IntegerField(u'host_collect_rate',
                                     validators=[
                                         validators.InputRequired(),
                                         validators.number_range(min=1,
                                                                 max=10000000)])
    host_reserve_time = IntegerField(u'host_reserve_time',
                                     validators=[
                                         validators.InputRequired(),
                                         validators.number_range(min=1,
                                                                 max=7)])
    host_id = IntegerField(u'host_id', validators=[])
    vm_collect_rate = IntegerField(u'vm_collect_rate',
                                   validators=[
                                       validators.InputRequired(),
                                       validators.number_range(min=1,
                                                               max=10000000)])
    vm_reserve_time = IntegerField(u'vm_reserve_time',
                                   validators=[
                                       validators.InputRequired(),
                                       validators.number_range(min=1, max=7)])
    vm_id = IntegerField(u'vm_id', validators=[])


class UpdateMonitorDataView(FormView):
    form_class = UpdateMonitorDataForm

    def post(self, *args, **kwargs):
        form = self.form_class()

        hcr = form.host_collect_rate.data
        hrt = form.host_reserve_time.data
        hostid = form.host_id.data

        vcr = form.vm_collect_rate.data
        vrt = form.vm_reserve_time.data
        vmid = form.vm_id.data

        if form.validate():
            # update monitor data
            cml_client = cml.get_client()
            values = cml_client.modify_monitor_template_config("/template/config", int(hcr), int(hrt), hostid)
            values = cml_client.modify_monitor_template_config("/template/config", int(vcr), int(vrt), vmid)
            return jsonify({})
        return jsonify({'errors': form.errors})
    
   
class UpdateMonitorTacticForm(NebulaForm):
    policy_operator = StringField(u'policy_operator', validators=[validators.input_required(),
                                            validators.length(min=1, max=30)])
    policy_limit= policy_id = IntegerField(u'policy_limit', validators=[])
    policy_duration= policy_id = IntegerField(u'policy_duration', validators=[])
    policy_id = IntegerField(u'policy_id', validators=[])
    
    
class UpdateMonitorTacticView(AuthorizedView):
    form_class = UpdateMonitorTacticForm
    
    def post(self, *args, **kwargs):
        form = self.form_class()
        policy_operator = form.policy_operator.data
        policy_limit = form.policy_limit.data
        policy_duration = form.policy_duration.data
        policy_id = form.policy_id.data
        LOG.info("UpdateMonitorTacticView_111:::::")
        LOG.info(policy_operator)
        LOG.info(policy_limit)
        LOG.info(policy_duration)
        LOG.info(policy_id)
        
        if form.validate():
            # TODO
            cml_client = cml.get_client()
            values = cml_client.modify_monitor_tactic( policy_id,policy_duration,policy_limit,policy_operator)
            return jsonify({"code": 0, "message": "success"})
        else:
            return jsonify({'errors': form.errors})