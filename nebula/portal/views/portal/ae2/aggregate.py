#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from flask import request
from flask import g
from wtforms import (
    StringField,
    TextAreaField,
    validators,
)

from nebula.core import Aggregate, ComputeNode
from nebula.core.forms.form import NebulaForm
from nebula.core.views import TemplateView
from nebula.core.db import session as db_session
from nebula.portal.views.base import (
    ListView,
    DetailView,
    UpdateView,
    BuilderCreateView,
    BuilderUpdateView,
    BuilderDeleteView,
)
from nebula.portal.views.portal.systems.base import SystemMixin
from nebula.core.mission.flows import (
    AggregateCreateBuilder,
    AggregateDeleteBuilder,
    AggregateUpdateBuilder,
    AggregateAddHostBuilder,
    AggregateRemoveHostBuilder,
)
from nebula.portal.views.portal.mixin import AggregateActiveMixin
from nebula.core.managers import managers

from nebula.core.i18n import _

LOG = logging.getLogger(__name__)

###############################################################################
# Forms
###############################################################################


class AggregateCreateForm(NebulaForm):
    name = StringField(_(u'集群名称'), validators=[validators.input_required(),
                                               validators.length(min=1, max=30)])
    description = TextAreaField(_(u'描述'),
                                validators=[validators.optional(),
                                            validators.Length(min=1, max=255)])
    zone = StringField(_(u'区域'),
                       validators=[validators.input_required(),
                                   validators.length(min=1, max=30)])
    def validate_name(self, name):
        name = name.data
        LOG.info(name)
        with db_session.transactional() as session:
            aggregate = session.query(Aggregate).filter_by(
                    name=name
                ).all()
            if aggregate:
                raise validators.ValidationError(_(u"集群名称[%s]已经被使用." % name))
        return name


class AggregateUpdateForm(NebulaForm):

    name = StringField(u'集群名称',
                       validators=[validators.input_required(),
                                   validators.length(min=1, max=30)])
    zone = StringField(u'可用域',
                       validators=[validators.input_required(),
                                   validators.length(min=1, max=30)])
    description = TextAreaField(u'描述',
                                validators=[validators.optional(),
                                            validators.length(min=1, max=255)])

    def validate_name(self, name):
        """
        修改要检查，除自己的名字外，有没有已存在的名字
        :param name:
        :return:
        """
        name = name.data
        LOG.info(name)
        with db_session.transactional() as session:
            aggregate = session.query(Aggregate).filter(
                    Aggregate.name == name,
                    Aggregate.id != self.request_kwargs["id"]
                ).all()
            if aggregate:
                raise validators.ValidationError(_(u"集群名称[%s]已经被使用." % name))
        return name


class AggregateAddHostForm(NebulaForm):
    aggregate_id = StringField(u'集群ID',
                               validators=[validators.input_required(),
                                           validators.length(min=1, max=30)])
    host_id = StringField(u'主机ID',
                          validators=[validators.input_required(),
                                      validators.length(min=1, max=30)])


class AggregateRemoveHostForm(AggregateAddHostForm):
    pass

###############################################################################
# CRUD
###############################################################################


class AggregateCreateFormView(TemplateView):
    template_name = 'aggregate/form/create_aggregate.html'


class AggregateCreateView(BuilderCreateView):
    form_class = AggregateCreateForm
    builder_class = AggregateCreateBuilder


class AggregateUpdateFormView(UpdateView):
    template_name = 'aggregate/form/update_aggregate.html'
    form_class = AggregateUpdateForm
    model_class = Aggregate


class AggregateUpdateView(BuilderUpdateView):
    form_class = AggregateUpdateForm
    builder_class = AggregateUpdateBuilder


class AggregateDeleteView(BuilderDeleteView):
    builder_class = AggregateDeleteBuilder


class AggregateDetailView(AggregateActiveMixin, DetailView):
    template_name = 'aggregate/aggregate_info.html'
    model_class = Aggregate


class AggregateListView(SystemMixin,AggregateActiveMixin, ListView):
    model_class = Aggregate
    search_fields = {
        'name': 'search'
    }

    def get_template_name(self):
        return 'aggregate/segment/aggregate_list.html'\
            if request.args.get("segment") else \
            'aggregate/aggregates.html'

###############################################################################
# EXTENDS
###############################################################################


class AggregateAddHostFormView(UpdateView):

    template_name = 'aggregate/form/add_host.html'
    form_class = AggregateAddHostForm
    model_class = Aggregate
    context_object_name = 'aggregate'

    def get_context_data(self, **kwargs):
        context = super(AggregateAddHostFormView, self).\
            get_context_data(**kwargs)
        hosts = managers.compute_nodes.get_available_hosts(g.context)
        added_hosts = managers.compute_nodes.\
            get_hosts_by_aggregate(g.context, self.kwargs.get)
        LOG.error(added_hosts)
        LOG.error(self.kwargs.get)
        context.update(dict(
            hosts=hosts,
            added_hosts_count=len(added_hosts)
        ))
        return context


class AggregateAddHostView(BuilderUpdateView):
    form_class = AggregateAddHostForm
    builder_class = AggregateAddHostBuilder


class AggregateRemoveHostFormView(UpdateView):

    template_name = 'aggregate/form/remove_host.html'
    form_class = AggregateRemoveHostForm
    model_class = Aggregate
    context_object_name = 'aggregate'

    builder_class = AggregateRemoveHostBuilder

    def get_context_data(self, **kwargs):
        context = super(AggregateRemoveHostFormView, self).\
            get_context_data(**kwargs)
        hosts = managers.compute_nodes.\
            get_hosts_by_aggregate(g.context, self.kwargs.get)
        context.update(dict(
            hosts=hosts
        ))
        return context


class AggregateRemoveHostView(BuilderUpdateView):
    form_class = AggregateRemoveHostForm
    builder_class = AggregateRemoveHostBuilder


class AggregateHostListView(ListView):

    template_name = 'aggregate/segment/host_list.html'
    model_class = ComputeNode
    order_by_fields = {
        "id": "desc",
        "created_at": "desc"
    }

    def get_context_data(self, **kwargs):
        context = super(AggregateHostListView,
                        self).get_context_data(**kwargs)
        aggregate_id = request.args.get("resource_id", None)
        context.update({
            "resource_id": aggregate_id,
            self.get_context_object_name(): self.get_queryset()
                .outerjoin(ComputeNode.aggregate)
                .filter(ComputeNode.aggregate_id == aggregate_id)
                .paginate(
                    page=self.get_page(),
                    per_page=self.get_per_page()
                )
        })
        return context
