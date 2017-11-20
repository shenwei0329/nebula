# -*- coding: utf-8 -*-

import logging

from nebula.core.models import Job
from nebula.core.managers.base import BaseManager

LOG = logging.getLogger(__name__)


class JobManager(BaseManager):

    def _get(self, context, id, session=None):
        return self.model_query(context, Job, session=session, user_only=False).get(id)

    def get(self, context, id):
        return self._get(context, id)

    def create(self, context, **kwargs):
        with self.transactional() as session:
            create_kwargs = {
                'creator_id': context.user_id,
                'owner_id': context.user_id,
            }
            create_kwargs.update(kwargs)
            job = Job(**create_kwargs)
            job.save(session)
        return job

    def update(self, context, job_id, values):
        with self.transactional() as session:
            job = self._get(context, job_id, session=session)
            job.update(values)

    def update_state_by_flow_uuid(self, context, flow_uuid, state):
        with self.transactional() as session:
            self.model_query(context, Job, session=session) \
                .filter(Job.flow_uuid == flow_uuid) \
                .update({'state': state})

    def get_recently_jobs(self, user_id=None, is_super=False, limit=5):
        with self.transactional() as session:
            query = session.query(Job)
            if not is_super:
                query = query.filter(Job.owner_id == user_id)
            result = query.order_by('-jobs.id').limit(limit).all()
        return result
