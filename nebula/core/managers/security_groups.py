# -*- coding: utf-8 -*-
from nebula.core.managers.base import BaseManager
from nebula.core.models import SecurityGroup, Port


class SecurityGroupManager(BaseManager):

    def _get(self, context, security_group_id, session=None):
        return self.model_query(context,
                                SecurityGroup,
                                session=session, user_only=False).filter_by(id=security_group_id).first()

    def get(self, context, security_group_id):
        return self._get(context, security_group_id)

    def _get_by_uuid(self, context, security_group_uuid, session=None):
        if not session:
            session = self.get_session()
        return self.model_query(context, SecurityGroup, session=session) \
                   .filter_by(security_group_uuid=security_group_uuid).first()

    def get_by_uuid(self, context, backup_uuid):
        return self._get_by_uuid(context, backup_uuid)

    def create(self, user_id, **kwargs):
        with self.transactional() as session:
            security_group = SecurityGroup(name=kwargs["name"],
                                           description=kwargs["description"],
                                           creator_id=user_id,
                                           owner_id=user_id)
            security_group.save(session)
        return security_group

    def update(self, context, security_group_id, **values):
        with self.transactional() as session:
            security_group = self._get(context, security_group_id, session)
            security_group.update(values)
        return security_group

    def delete_by(self, **kwargs):
        with self.transactional() as session:
            session.query(SecurityGroup).filter_by(**kwargs).delete()

    def list(self):
        with self.transactional() as session:
            return session.query(SecurityGroup).filter_by()

    def availables(self, context, **kwargs):
        return self.model_query(context, SecurityGroup, **kwargs).filter(
            SecurityGroup.security_group_uuid != None
        ).all()
    
    def filter_by(self, **values):
        with self.transactional() as session:
            return session.query(SecurityGroup).filter_by(**values).all()
    
    def except_by(self, **values):
        with self.transactional() as session:
            port_id = values.get("port_id")
            sgroup_id = values.get("sgroup_id")
            return session.query(SecurityGroup).join(Port.security_group).\
                filter(SecurityGroup.id != sgroup_id).\
                filter(Port.id == port_id).all()

    def count_all(self):
        with self.transactional() as session:
            result = session.query(SecurityGroup).filter().count()
        return result or 0
    

