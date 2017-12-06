#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#

import sys

"""表字典
"""
TableDic = {
    'MEMBER': 'member_t',
    'DATAELEMENT':'data_element_t',
    'PROJECT':'project_t',
    'PRODUCT':'product_t',
    'TASK':'task_t',
    'ENGINERRING':'enginerring_t',
    'DELIVERY':'delivery_t',
    'REQUIRMENT':'requirment_t',
    'TESTRECORD':'testrecord_t',
    'MEETING':'meeting_t',
    'MEMBERALIAS':'member_alias_t',
    'CHECKON':'checkon_t',
    'PD_MANAGEMENT':'pd_management_t',
    'PD_GROUP':'pd_group_t',
    'PD_GROUP_MEMBER':'pd_group_member_t',
    'RISK_MANAGEMENT':'risk_t',
    'EVENT': 'event_t',
    'PROJECT_KEY':'project_key_t',
    'PROJECT_TASK':'project_task_t'
}

"""设置字符集
"""
reload(sys)
sys.setdefaultencoding('utf-8')

import json
from datetime import datetime

def main():

    global TableDic

    f = open('/home/shenwei/nebula/python-proc/tabledic.conf','w')
    s = json.dumps(TableDic)
    f.write(s)
    f.close()

if __name__ == '__main__':
    while True:
        if not main():
            break

#
# Eof
