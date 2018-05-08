# -*- coding: utf-8 -*-
import itertools

import arrow
from flask import request

from nebula.core import (
    Job,
    constants,
)
from nebula.portal.views.base import (
    ListView,
    JsonListView,
)
from nebula.portal.decorators.auth import require_auth


class JobSubListView(ListView):

    model_class = Job
    template_name = 'job/segment/job_sub_list.html'
    filter_fields = {
        'resource_type': 'resource_type',
        'resource_id': 'resource_id',
    }

    def get_context_data(self, **additional_context):
        context = super(JobSubListView, self).\
            get_context_data(**additional_context)
        context.update({
            'resource_id': request.args.get('resource_id'),
            'resource_type': request.args.get('resource_type'),
        })
        return context


class JobListView(ListView):

    model_class = Job
    filter_fields = {
        'resource_type': 'resource_type',
        'resource_id': 'resource_id',
    }

    def get_template_name(self):
        return 'job/segment/job_list.html' \
            if request.args.get('segment') \
            else 'job/jobs.html'


class JobJsonListView(JsonListView):
    decorators = (require_auth, )
    model_class = Job
    list_feilds = [
        'id',
        'creator_id',
        'owner_id',
        'resource_id',
        'resource_type',
        'resource_name',
        'access_url',
        'flow_name',
        'state',
        'display_desc',
        'created_at',
        'updated_at',
    ]
    order_by_fields = {
        'id': 'asc',
    }

    # def get_queryset(self):
    #     query = super(JobJsonListView, self).get_queryset()
    #     duration = -int(request.args.get('duration', '5'))
    #     return query.filter(
    #         self.model_class.created_at >= arrow.utcnow().
    #         replace(minutes=duration).datetime
    #     )

    def get_queryset(self):
        query = super(JobJsonListView, self).get_queryset()
        duration = -int(request.args.get('duration', '5'))
        return query.filter(
            self.model_class.created_at >= arrow.utcnow().
            replace(minutes=duration).datetime
        )

    def get_context_data(self, **additional_context):
        context = super(JobJsonListView, self).\
            get_context_data(**additional_context)
        unfinished_job_count = len(
            filter(
                lambda j: j['state'] in constants.JOB_STATUS_RUNNING_LIST,
                context[self.get_context_object_name()]
            )
        )
        context.update({'unfinished_job_count': unfinished_job_count})
        return context

    def get_ordered_queryset(self):
        jobs = super(JobJsonListView, self).get_ordered_queryset()

        _get_key = lambda o: (o.resource_id, o.resource_type)
        jobs = sorted(jobs, key=_get_key)
        group_result = itertools.groupby(jobs,
                                         key=_get_key)
        return (
            max(items, key=lambda j: j.created_at)
            for _, items in group_result
        )
