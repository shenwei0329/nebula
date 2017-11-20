# -*- coding: utf-8 -*-
import random
import string
import uuid

from nebula.core.managers import managers
from nebula.core.managers.base import BaseManager
from nebula.core.db import session as db_session
from nebula.core.models import Aggregate

get_random_string = lambda y: "".join(
    map(lambda x: random.choice(string.ascii_letters), range(y)))


class AggregateManager(BaseManager):

    def _get(self, context, id, session=None):
        return self.model_query(context, Aggregate, session=session, user_only=False).get(id)

    def get(self, context, id):
        return self._get(context, id)

    def get_by_name(self, context, name):
        with self.transactional() as session:
            result = self.model_query(context, Aggregate, session=session, user_only=False).\
                filter(Aggregate.name == name).one()
            return result

    def all(self, context, user_only=True):
        return self.model_query(context, Aggregate, user_only=user_only).all()

    def availables(self, context):
        aggregates = self.all(context, user_only=False)
        return filter(lambda a: a.has_compute_nodes, aggregates)

    def create(self, user_id, **kwargs):
        aggregate_uuid = str(uuid.uuid1())

        with self.transactional() as session:
            aggregate = Aggregate(aggregate_uuid=aggregate_uuid,
                                  name=kwargs.get("name"),
                                  description=kwargs.get("description"),
                                  zone=kwargs.get("zone"),
                                  creator_id=user_id,
                                  owner_id=user_id)
            aggregate.save(session)
            return aggregate

    def delete(self, aggregate):
        with self.transactional() as session:
            if isinstance(aggregate, (int, long)):
                aggregate = session.query(Aggregate).get(aggregate)
            session.delete(aggregate)

    def update(self, context, aggregate_id, values):
        with self.transactional() as session:
            aggregate = self._get(context, aggregate_id, session=session)
            aggregate.update(values)
        return aggregate

    def count_all(self):
        with self.transactional() as session:
            result = session.query(Aggregate).filter().count()
        return result
