# -*- coding: utf-8 -*-

from nebula.core.managers.base import BaseManager
from nebula.core.models import Alarm
from nebula.core.models import Alarm_rule
from nebula.core.models import Alarm_binding
from nebula.core.db import session as db_session

class AlarmManager(BaseManager):

    def _get(self, context, alarm_id, session=None):
        return self.model_query(
            context, Alarm, session=session, user_only=False
        ).filter_by(id=alarm_id).first()

    def get(self, context, alarm_id):
        return self._get(context, alarm_id)

    def get_by(self, context, **params):
        return self.model_query(
            context, Alarm
        ).filter_by(**params).all()

    def get_available(self, context, **params):
        with db_session.transactional() as session:
            alarm_unavailable = session.query(Alarm).join(Alarm_binding.alarm).all()
            alarm_all = self.model_query(context, Alarm).filter_by(**params).all()
            alarm_available = list(set(alarm_all) - set(alarm_unavailable))

        return alarm_available

    def get_all(self, context, user_only=False):
        return self.model_query(context, Alarm, user_only=user_only).all()
    
    def filter_by(self, **kwargs):
        with self.transactional() as session:
            return session.query(Alarm).filter_by(**kwargs)

    def create(self, name, description, type, enabled, repeat_actions, state,
               state_timestamp, timestamp, threshold_rule, creator):
        with self.transactional() as session:
            alarm = Alarm(
                name=name,
                description=description,
                type=type,
                enabled=enabled,
                repeat_actions=repeat_actions,
                state=state,
                state_timestamp=state_timestamp,
                timestamp=timestamp,
                combination_rule=None,
                threshold_rule=threshold_rule,
                time_constraints=None,
                creator_id=creator,
                owner_id=creator
            )
            alarm.save(session)
        return alarm

    def update(self, context, alarm_id, values):
        with self.transactional() as session:
            alarm = self._get(context, alarm_id, session=session)
            alarm.update(values)

    def delete(self, alarm_id):
        result = dict(
            code=1,
            message=u'success'
        )
        with self.transactional() as session:
            alarm = session.query(Alarm).\
                filter(Alarm.id == alarm_id).first()
            if not alarm:
                result.update(dict(
                    code=0,
                    message=u'Not Found Alarm.'
                ))
                return result
            session.delete(alarm)
        return result


class AlarmRuleManager(BaseManager):

    def _get(self, context, rule_id, session=None):
        return self.model_query(
            context, Alarm_rule, session=session, user_only=False
        ).filter_by(id=rule_id).first()

    def get(self, context, rule_id):
        return self._get(context, rule_id)

    def get_by(self, context, **params):
        return self.model_query(
            context, Alarm_rule
        ).filter_by(**params).all()

    def get_count_by(self, context, **params):
        return self.model_query(
            context, Alarm_rule
        ).filter_by(**params).count()

    def create(self, creator, meter_name, alarm_id, comparison_operator, threshold, alarm_actions, ok_actions,
               insufficient_data_actions, start, evaluation_periods=1, query='empty', period=120,
               exclude_outlier=False, statistic='max'):
        with self.transactional() as session:
            rule = Alarm_rule(
                meter_name=meter_name,
                alarm_id=alarm_id,
                comparison_operator=comparison_operator,
                threshold=threshold,
                alarm_actions=alarm_actions,
                ok_actions=ok_actions,
                insufficient_data_actions=insufficient_data_actions,
                evaluation_periods=evaluation_periods,
                period=period,
                query=query,
                exclude_outlier=exclude_outlier,
                start=start,
                statistic=statistic,
                creator_id=creator,
                owner_id=creator
            )
            rule.save(session)
        return rule

    def update(self, context, rule_id, values):
        with self.transactional() as session:
            rule = self._get(context, rule_id, session=session)
            rule.update(values)

    def delete(self, rule_id):
        result = dict(
            code=1,
            message=u'success'
        )
        with self.transactional() as session:
            rule = session.query(Alarm_rule).\
                filter(Alarm_rule.id == rule_id).first()
            if not rule:
                result.update(dict(
                    code=0,
                    message=u'Not Found Alarm Rule.'
                ))
                return result
            session.delete(rule)
        return result

class AlarmBindingManager(BaseManager):

    def _get(self, context, binding_id, session=None):
        return self.model_query(
            context, Alarm_binding, session=session, user_only=False
        ).filter_by(id=binding_id).first()

    def get(self, context, binding_id):
        return self._get(context, binding_id)

    def get_by(self, context, **params):
        return self.model_query(
            context, Alarm_binding
        ).filter_by(**params).all()

    def create(self, alarm_tmpl_id, creator, rule_id, alarm_cml_id, instance_id):
        with self.transactional() as session:
            binding = Alarm_binding(
                alarm_tmpl_id=alarm_tmpl_id,
                rule_id=rule_id,
                alarm_cml_id=alarm_cml_id,
                instance_id=instance_id,
                creator_id=creator,
                owner_id=creator
            )
            binding.save(session)
        return binding

    def update(self, context, binding_id, values):
        with self.transactional() as session:
            rule = self._get(context, binding_id, session=session)
            rule.update(values)

    def delete(self, binding_id):
        result = dict(
            code=1,
            message=u'success'
        )
        with self.transactional() as session:
            binding = session.query(Alarm_binding).\
                filter(Alarm_binding.id == binding_id).first()
            if not binding:
                result.update(dict(
                    code=0,
                    message=u'Not Found Alarm Binding.'
                ))
                return result
            session.delete(binding)
        return result

    def delete_by(self, **params):
        result = dict(
            code=1,
            message=u'success'
        )
        with self.transactional() as session:
            binding = session.query(Alarm_binding).\
                filter_by(**params).first()
            if not binding:
                result.update(dict(
                    code=0,
                    message=u'Not Found Alarm Binding.'
                ))
                return result
            session.delete(binding)
        return result