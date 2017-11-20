# -*- coding: utf-8 -*-

import logging

from nebula.core.models import Alert
from nebula.core.managers.base import BaseManager
from sqlalchemy import or_

LOG = logging.getLogger(__name__)


class AlertManager(BaseManager):

    def get_user_all(self, context, user_only=False):
        query = self.model_query(context, Alert, user_only=True).filter( or_(Alert.readed == None ,  Alert.readed !=1  ) )\
            .order_by('alerts.created_at desc')
        return query

    def create(self, **kwargs):
        with self.transactional() as session:
            create_kwargs = dict()
            create_kwargs.update(kwargs)
            alert = Alert(**create_kwargs)
            alert.save(session)
            return alert

    def make_all_read(self,context):
        LOG.info("[begin]: make all read alert message")
        query = self.model_query(context, Alert, user_only=True)
        query.update({
                Alert.readed: '1'
            })
        LOG.info("[end]: make all read alert message")