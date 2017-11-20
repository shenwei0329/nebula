# -*- coding: utf-8 -*-
import logging

from nebula.core.models import Meters
from nebula.core.managers.base import BaseManager



LOG = logging.getLogger(__name__)


class AlarmMeters(BaseManager):
    def _get(self, context, id, session=None):
        if not session:
            session = self.get_session()
        return self.model_query(context, Meters, session=session, user_only=False).get(id)

    def get(self, context, id):
        return self._get(context, id)

    def get_by(self, context, **params):
        return self.model_query(
            context, Meters
        ).filter_by(**params).all()

    def get_enabled(self, context, user_only=False):
        return self.model_query(
            context, Meters, user_only=user_only
        ).filter_by(state=True).all()
        
    def get_all(self, context, user_only=False):
        return self.model_query(context, Meters, user_only=user_only).all()

    def update(self, context, id, values):
        with self.transactional() as session:
            meter = self._get(context, id, session=session)
            meter.update(values)
        return meter

    def create(self, **meter):
        with self.transactional() as session:
            meter = Meters(**meter)
            meter.save(session)
        return meter



