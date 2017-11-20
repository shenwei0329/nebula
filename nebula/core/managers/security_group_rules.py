# -*- coding: utf-8 -*-
from sqlalchemy.orm import joinedload
from nebula.core.managers.base import BaseManager
from nebula.core.models import SecurityGroupRule


class SecurityGroupRuleManager(BaseManager):

    def _get(self, context, security_group_rule_id, session=None):
        return self.model_query(context,
                                SecurityGroupRule,
                                session=session, user_only=False)\
            .options(joinedload(SecurityGroupRule.security_group))\
            .filter_by(id=security_group_rule_id).first()

    def get(self, context, security_group_rule_id):
        return self._get(context, security_group_rule_id)

    def create(self, user_id, **kwargs):
        with self.transactional() as session:
            security_group_rule = SecurityGroupRule(
                security_group_id=kwargs["security_group_id"],
                name=kwargs["name"],
                direction=kwargs["direction"],
                protocol=kwargs["protocol"],
                port_range_min=kwargs["port_range_min"],
                port_range_max=kwargs["port_range_max"],
                remote_ip_prefix=kwargs["remote_ip_prefix"],
                security_group_rule_uuid=kwargs.get("security_group_rule_uuid", None),
                creator_id=user_id,
                owner_id=user_id
            )
            security_group_rule.save(session)
        return security_group_rule

    def update(self, context, security_group_rule_id, values):
        with self.transactional() as session:
            security_group_rule = self._get(context,
                                            security_group_rule_id, session)
            security_group_rule.update(values)
        return security_group_rule

    def delete_by(self, **kwargs):
        with self.transactional() as session:
            session.query(SecurityGroupRule).filter_by(**kwargs).delete()

    def list(self):
        with self.transactional() as session:
            return session.query(SecurityGroupRule).filter_by()
