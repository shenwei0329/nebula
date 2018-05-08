# -*- coding: utf-8 -*-
from nebula.core.common.propertyutils import cached_property
from nebula.openstack.common import importutils

MANAGER_NAMESPACE_PREFIX = 'nebula.core.managers'

def _full_qualified(name):
    name = name.replace(':', '.')
    return '%s.%s' % (MANAGER_NAMESPACE_PREFIX, name)

class _Managers(object):
    """
    2015.7.27 shenwei @ChengDu

        从 core.managers 下装载模块

    """

    _event_listened = False # 是否已监听过Event

    @staticmethod
    def _import_and_initialize(name):
        klass = importutils.import_class(_full_qualified(name))

        if hasattr(klass, '__declare_last__'):
            klass.__declare_last__()
        return klass()

    @cached_property
    def etlmod(self):
        return self._import_and_initialize(
            'etlmod:EtlManager')

    @cached_property
    def datamngmod(self):
        return self._import_and_initialize(
            'datamngmod:DataElement')

    @cached_property
    def upfilemod(self):
        return self._import_and_initialize(
            'upfilemod:upfilemod')

    @cached_property
    def membermod(self):
        return self._import_and_initialize(
            'membermod:membermod')

    @cached_property
    def projectmod(self):
        return self._import_and_initialize(
            'projectmod:projectmod')

    @cached_property
    def productmod(self):
        return self._import_and_initialize(
            'productmod:productmod')

    @cached_property
    def taskmod(self):
        return self._import_and_initialize(
            'taskmod:taskmod')

    @cached_property
    def enginerringmod(self):
        return self._import_and_initialize(
            'enginerringmod:enginerringmod')

    @cached_property
    def deliverymod(self):
        return self._import_and_initialize(
            'deliverymod:deliverymod')

    def register_listeners(self):
        """
        开始监听所有Managers cache event
        :return:
        """
        if not self._event_listened:
            self.virtualrouters.count_cache.listen_events()

            self._event_listened = True

managers = _Managers()
