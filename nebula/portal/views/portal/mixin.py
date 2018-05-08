# -*- coding: utf-8 -*-


"""
Active Mixin
"""


class HostActiveMixin(object):

    active_module = 'host'


class AggregateActiveMixin(object):

    active_module = 'aggregate'


class InstanceActiveMixin(object):

    active_module = 'instance'


class BackupActiveMixin(object):

    active_module = 'backup'


class ImageActiveMixin(object):

    active_module = 'image'


class FirewallActiveMixin(object):

    active_module = 'firewall'


class NetworkActiveMixin(object):

    active_module = 'network'


class VolumeActiveMixin(object):

    active_module = 'volume'


class MonitorActiveMixin(object):
    active_module = 'monitor'

    def __init__(self, *args, **kwargs):
        super(MonitorActiveMixin, self).__init__(*args, **kwargs)
        self.main_menus_mini = True

class AlarmMeterActiveMixin(object):
    active_module = 'alarm_meters'

class AlarmActiveMixin(object):
    active_module = 'alarms'

class ZoneActiveMixin(object):
    active_module = 'zones'