# -*- coding: utf-8 -*-

"""
define portal navigation's items
"""

TOTLE_MENUS = [
    {
        'local_name': u'总概况',
        'en_name': 'TotalInfo',
        'active': False,
        'icon': 'icon-home',
        'endpoint': 'portal.empty',
        'module': 'totalinfo',
    },
    {
        'local_name': u'项目概况',
        'en_name': 'TotalInfo',
        'active': False,
        'icon': 'icon-home',
        'endpoint': 'portal.empty',
        'module': 'totalinfo',
    },
    {
        'local_name': u'产品概况',
        'en_name': 'TotalInfo',
        'active': False,
        'icon': 'icon-home',
        'endpoint': 'portal.empty',
        'module': 'totalinfo',
    },
    {
        'local_name': u'资源概况',
        'en_name': 'TotalInfo',
        'active': False,
        'icon': 'icon-home',
        'endpoint': 'portal.empty',
        'module': 'totalinfo',
    },
]

PROJECT_MENUS = [
    {
        'local_name': u'',
        'en_name': 'TotalInfo',
        'active': False,
        'icon': 'icon-home',
        'endpoint': 'portal.empty',
        'module': 'totalinfo',
    },
    {
        'local_name': u'项目概况',
        'en_name': 'TotalInfo',
        'active': False,
        'icon': 'icon-home',
        'endpoint': 'portal.empty',
        'module': 'totalinfo',
    },
    {
        'local_name': u'产品概况',
        'en_name': 'TotalInfo',
        'active': False,
        'icon': 'icon-home',
        'endpoint': 'portal.empty',
        'module': 'totalinfo',
    },
    {
        'local_name': u'资源概况',
        'en_name': 'TotalInfo',
        'active': False,
        'icon': 'icon-home',
        'endpoint': 'portal.empty',
        'module': 'totalinfo',
    },
]

DATAMANAGEMENT_MENUS = [
    {
        'local_name': u'总览',
        'en_name': 'TotalInfo',
        'active': False,
        'icon': 'icon-home',
        'endpoint': 'portal.empty',
        'module': 'totalinfo',
    },
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
]

def setMenus():
    context = dict(
        totle_menus=TOTLE_MENUS,
        project_menus=DATAMANAGEMENT_MENUS,
        product_menus=DATAMANAGEMENT_MENUS,
        resource_menus=DATAMANAGEMENT_MENUS,
        datamng_menus=DATAMANAGEMENT_MENUS,
    )
    return context
