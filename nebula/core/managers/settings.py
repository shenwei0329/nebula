# -*- coding: utf-8 -*-

import copy
import logging

from oslo.config import cfg

from nebula.core.models import SystemProperty
from nebula.core.managers import managers
from nebula.core.db import session as db_session
from .base import BaseManager

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

CONF.import_group("quota", 'nebula.core.quota')


class SettingManager(BaseManager):

    @staticmethod
    def whole_quotas():
        return [
            'instance_attach_volumes',
            'instance_attach_ports',
            'instance_backups',
            'volume_backups',
        ]

    @classmethod
    def create_update_setting(cls, **kwargs):
        subjects = copy.copy(kwargs)
        with db_session.transactional() as session:
            quotas = cls.whole_quotas()
            for key, value in subjects.iteritems():
                query = session.query(SystemProperty).filter_by(key=key)
                result = query.first()
                if result:
                    query.update({'value': value})
                else:
                    system_property = SystemProperty(key=key, value=value)
                    system_property.save(session)
                if key in quotas:
                    managers.quotas.create_quota_class(resource=key,
                                                       hard_limit=value)

    @classmethod
    def get_settings(cls):
        with db_session.transactional() as session:
            query_set = session.query(SystemProperty).all()
            settings = {}
            for item in query_set:
                settings.update({
                    item.key: item.value
                })
            if settings and "instance_attach_volumes" in settings.keys():
                return settings
            default_settings = cls._import_default_settings()
            settings.update(default_settings)
            settings.update(settings)
        return settings

    @classmethod
    def get_setting_by(cls, key=None):
        settings = cls.get_settings()
        if not key or key not in settings:
            return settings
        else:
            return settings[key]

    @classmethod
    def _import_default_settings(cls):
        settings = {}
        settings.update(cls._get_conf_value('instance_attach_volumes'))
        settings.update(cls._get_conf_value('instance_attach_ports'))
        settings.update(cls._get_conf_value('instance_backups'))
        settings.update(cls._get_conf_value('instance_cores_min'))
        settings.update(cls._get_conf_value('instance_cores_max'))
        settings.update(cls._get_conf_value('instance_ram_max'))
        settings.update(cls._get_conf_value('instance_ram_min'))
        settings.update(cls._get_conf_value('instance_batches'))
        settings.update(cls._get_conf_value('volume_backups'))
        settings.update(cls._get_conf_value('volume_capacity'))
        settings.update(cls._get_conf_value('network_vlan_min'))
        settings.update(cls._get_conf_value('network_vlan_max'))
        settings.update(cls._get_conf_value('instance_batches'))
        return settings

    @classmethod
    def _get_conf_value(cls, item):
        conf_item_name = 'quota_{0}'.format(item)
        return {
            item: CONF.quota.get(conf_item_name)
        }
