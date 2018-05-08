# -*- coding: utf-8 -*-

resources = {
    'cores': u'VCPU',
    'instances': u'虚拟机数',
    'disk': u'磁盘',
    'ram': u'内存',
    'virtual_routers': u'虚拟路由',
    'bandwidth': u'宽带',
    'binding_private_networks': u'绑定私有网络',
    'binding_publicips': u'绑定公有IP',
    'bandwidth_rx': u'带宽下行',
    'bandwidth_tx': u'带宽上行',
}

resources_unit = {
    'cores': u'个',
    'instances': u'个',
    'disk': u'G',
    'ram': u'M',
    'virtual_routers': u'个',
    'bandwidth': u'M',
    'binding_private_networks': u'个',
    'binding_publicips': u'个',
    'bandwidth_rx': u'M',
    'bandwidth_tx': u'M',
}


def quota_resource_cn_name(resource):

    return resources.get(resource, resource)


def quota_unit(resource):
    return resources_unit.get(resource, u'M')


def quota_default_value(resource, quotas):
    if resource in quotas.keys():
        return quotas[resource]['hard_limit']
    else:
        return None