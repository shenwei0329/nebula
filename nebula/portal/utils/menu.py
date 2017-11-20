# -*- coding: utf-8 -*-

"""
define portal navigation's items
"""

DATAMANAGEMENT_MENUS = [
    {
        'local_name': u'数据录入',
        'en_name': 'DataIn',
        'active': False,
        'icon': 'icon-home',
        'endpoint': 'portal.cdh',
        'module': 'datain',
    },
    {
        'local_name': u'基础数据浏览',
        'en_name': 'DataManagement',
        'active': False,
        'icon': 'icon-book',
        'endpoint': 'portal.datamng',
        'module': 'datamanage',
    },
    {
        'local_name': u'作业管理',
        'en_name': 'JobManagement',
        'active': False,
        'icon': 'icon-calendar',
        'endpoint': 'portal.etltools',
        'module': 'jobmanage',
    },
    {
        'local_name': u'音乐类型识别',
        'en_name': 'Music',
        'active': False,
        'icon': 'icon-music',
        'endpoint': 'portal.music',
        'module': 'jobmanage',
    },
]

def setMenus():
    context = dict(
        datamng_menus=DATAMANAGEMENT_MENUS,
    )
    return context
