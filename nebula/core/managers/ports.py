# -*- coding: utf-8 -*-

from sqlalchemy.orm import joinedload
from nebula.core import constants
from nebula.core.managers.base import BaseManager
from nebula.core.models import (
    Subnet,
    Port,
    SecurityGroupPort,
    SecurityGroup,
    Network
)

import logging
LOG = logging.getLogger(__name__)


class PortManager(BaseManager):

    def _get(self, context, port_id, session=None):
        return self.model_query(context, Port, session=session, user_only=False).\
            options(joinedload(Port.network)).filter_by(id=port_id).first()

    def get(self, context, port_id):
        return self._get(context, port_id)

    def create(self, creator_id, **kwargs):
        subnet = Subnet.query.get(kwargs["subnet_id"])
        net = Network.query.get(kwargs["network_id"])

        fixed_ip_param = {}
        if "ip" in kwargs:
            if kwargs["ip"]:
                fixed_ip_param["ip_address"] = kwargs["ip"]
        fixed_ip_param["subnet_id"] = subnet.subnet_uuid
                
        fixed_ips = [fixed_ip_param]
        params = {}
        if "mac_addr" in kwargs:
            if kwargs["mac_addr"]:
                params["mac_address"] = kwargs["mac_addr"]
                
        if "name" in kwargs:
            if kwargs["name"]:
                params["name"] = kwargs["name"]
            else:
                params.update(dict(name=net.name))
        else:
            params.update(dict(name=net.name))

        params["status"] = constants.PORT_STATUS_BUILD
        params["fixed_ips"] = fixed_ips
        params["subnet_id"] = subnet.id
        params["network_id"] = kwargs["network_id"]
        params["instance_id"] = kwargs["instance_id"]
        params["creator_id"] = creator_id
        params["owner_id"] = creator_id
        
        with self.transactional() as session:
            port = Port(**params)
            port.save(session)
        return port

    def create_(self, context, **kwargs):
        with self.transactional() as session:
            port = Port(**kwargs)
            port.save(session)
        return port

    def update(self, context, port_id, **values):
        with self.transactional() as session:
            port = self._get(context, port_id, session)
            security_group_id = values.pop("security_group_id", None)
            port.update(values)
            if security_group_id:
                temp = SecurityGroupPort(port_id=port_id,
                                         security_group_id=security_group_id)
                port.security_group.append(temp)
        return port

    def delete(self, port_id):
        with self.transactional() as session:
            session.query(Port).filter_by(id=port_id).delete()

    def filter_by(self, **kwargs):
        with self.transactional() as session:
            result = session.query(Port).\
                options(joinedload(Port.network)).filter_by(**kwargs).all()
        return result
    
    def joined_by_security_group(self, **kwargs):
        with self.transactional() as session:
            result = session.query(Port).\
                options(joinedload(Port.security_group)).\
                filter_by(**kwargs).all()
        return result
    
    def joined_by_sgroup_port(self, **kwargs):
        with self.transactional() as session:
            result = session.query(SecurityGroup).\
                join(SecurityGroupPort).\
                filter(SecurityGroupPort.port_id == kwargs['id']).all()
        return result
    
    def detach_security_group(self, context, port_id, **values):
        with self.transactional() as session:
            port = self._get(context, port_id, session)
            security_group_id = values.pop("security_group_id", None)
            session.query(SecurityGroupPort).filter_by(port_id=port_id).delete()
            port.update(values)
           
        return port

    def is_ip_exists(self, context, ip_address):
        with self.transactional() as session:
            q = session.query(Port).\
                filter(Port.fixed_ips.op('regexp')(r'[[:<:]]%s[[:>:]]' % ip_address))
            return session.query(q.exists()).scalar()
    
    def detach_by_security_group(self, context, port_id, **values):
        with self.transactional() as session:
            port = self._get(context, port_id, session)
            sgroup_id = values.pop("security_group_id", None)
            session.query(SecurityGroupPort).\
                filter_by(security_group_id=sgroup_id).\
                filter_by(port_id=port_id).delete()
            port.update(values)

        return port
