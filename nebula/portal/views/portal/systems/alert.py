# -*- coding: utf-8 -*-
import logging
from flask import request
from flask import jsonify
from flask.views import MethodView
import json
import time
from nebula.core.managers import managers
LOG = logging.getLogger(__name__)

#from nebula.portal.decorators.auth import require_auth

class SystemAlertView(MethodView):

    def post(self, *args, **kwargs):
        result = dict(
            code=200,
            message='succeed'
        )
    #    if kwargs['type'].lower().find('vm') >= 0:
    #      type_s=u'虚拟机'
    #    elif kwargs['type'].lower().find('host') >= 0:
    #        type_s=u'主机'

        type_s = kwargs['type'].lower()
        rules = managers.alarm_rules.get({}, kwargs['rule_id'])
        if rules:
            if rules.meter_name.lower().find('cpu') >= 0:
                meter_type_s = u'CPU使用率'
            elif rules.meter_name.lower().find('disk') >=0:
                meter_type_s = u'硬盘使用率'
            else:
                meter_type_s = u'内存使用率'

        if rules.comparison_operator.find('gt')>=0:
            gt_lt = u'大于'
        else:
            gt_lt = u'小于'


        

        if type_s and meter_type_s and (kwargs['alarm_type'].find('alarm')>=0):
            threshold = ('%d' %rules.threshold)
            desc= (type_s + ' ' + meter_type_s + gt_lt + threshold +'%')
        elif type_s and meter_type_s and (kwargs['alarm_type'].find('ok')>=0):
            threshold = ('%d' %rules.threshold)
            desc= (type_s + ' ' + meter_type_s + u'正常')
        else:
            desc= (type_s + ' ' + meter_type_s + u'没有取到数据')

        ins_uuid=kwargs['id']
        
        name_s=''
        owner_id=''
        res_id=''
        if type_s.find('vm') >= 0:
            instances = managers.instances.get_by_uuid({}, ins_uuid)
            if instances:
                name_s=instances.display_name
                owner_id=instances.owner_id
                res_id=instances.id
        elif type_s.find('host') >= 0:
            host= managers.compute_nodes.get({},ins_uuid)
            if host:
                name_s=host.hostname
                owner_id=host.owner_id
                res_id=host.id
        
        if (kwargs['alarm_type'].find('alarm')>=0 and rules.alarm_actions):
            priority_key = '4'
        elif (kwargs['alarm_type'].find('ok')>=0 and rules.ok_actions):
            priority_key = '1'
        elif (kwargs['alarm_type'].find('alarm')>=0 and rules.insufficient_data_actions):
            priority_key = '2'
        else:
            priority_key = '4'

        if (kwargs['alarm_type'].find('alarm')>=0 and rules.alarm_actions) or (kwargs['alarm_type'].find('ok')>=0 and rules.ok_actions) or (kwargs['alarm_type'].find('alarm')>=0 and rules.insufficient_data_actions):
            managers.alert.create(name=type_s,
                                  prioritykey=priority_key,
                                  resource_name=name_s,
                                  key2=rules.meter_name,
                                  value=rules.threshold,
                                  description=desc,
                                  time=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())),
                                  resource_id=res_id,
                                  type2='external',
                                  priorityname='严重',
                                  unit='%',
                                  polices_id=' ',
                                  owner_id=owner_id
            )
        return jsonify(result)
