# -*- coding: utf-8 -*-

from .base import BaseManager

SYSTEM_PROPERTIES = {
    'instance_hard_attach_disk': 60,
    'instance_hard_attach_port': 60,
    'instance_hard_backup': 60,
    'instance_min_vcpu_cores': 1,
    'instance_max_vcpu_cores': 60,
    'instance_min_ram': 256,
    'instance_max_ram': 1024 * 50,
    'volume_hard_backup': 60,
    'volume_hard_size': 10000,
    'network_min_vlan': 2,
    'network_max_vlan': 100
}


class SystemPropertyManager(BaseManager):
    pass


class UserPropertyManager(BaseManager):
    pass