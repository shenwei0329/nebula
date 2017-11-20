# -*- coding: utf-8 -*-
import netaddr
from sqlalchemy import types

from nebula.openstack.common import jsonutils


class UUID(types.TypeDecorator):
    impl = types.CHAR

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.CHAR(36))


class IPAddress(types.TypeDecorator):
    impl = types.String

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.String(39))

    def process_bind_param(self, value, dialect):
        """Process/Formats the value before insert it into the db."""
        if self.is_valid_ipv6(value):
            return self.get_shortened_ipv6(value)
        return value

    @staticmethod
    def is_valid_ipv6(address):
        try:
            return netaddr.valid_ipv6(address)
        except netaddr.AddrFormatError:
            return False

    @staticmethod
    def get_shortened_ipv6(address):
        addr = netaddr.IPAddress(address, version=6)
        return str(addr.ipv6())


class Json(types.TypeDecorator):
    impl = types.Text

    def process_bind_param(self, value, dialect):
        if value:
            return jsonutils.dumps(value)
        else:
            return None

    def process_result_value(self, value, dialect):
        if value:
            return jsonutils.loads(value)
        else:
            return None
