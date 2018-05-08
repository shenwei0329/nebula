# -*- coding: utf-8 -*-
from flask import request

from oslo_config import cfg

from .base import View
from .base import TemplateResponseMixin


CONF = cfg.CONF
CONF.import_group('portal', 'nebula.portal.options')


class MultipleObjectMixin(object):

    model_class = None

    filter_fields = {}
    search_fields = {}
    order_by_fields = {
        'id': 'desc',
    }

    page_argument = 'page'
    per_page_argument = 'per_page'

    context_object_name = None

    def get_filter_fields(self):
        filter_fields = {}

        for field_name, mapping_name in self.filter_fields.items():
            if request.args.get(mapping_name) is not None:
                filter_fields[field_name] = request.args[mapping_name]
            if self.kwargs.get is not None:
                filter_fields[field_name] = self.kwargs[mapping_name]

        return filter_fields

    def get_search_fields(self):
        search_fields = {}

        for field_name, mapping_name in self.search_fields.items():
            if request.args.get(mapping_name) is not None:
                search_fields[field_name] = request.args[mapping_name]
        return search_fields

    def get_queryset(self):
        return self.model_class.query

    def get_filtered_queryset(self):
        filter_fields_dict = self.get_filter_fields()
        if not filter_fields_dict:
            return self.get_queryset()
        return self.get_queryset().filter_by(**filter_fields_dict)

    def get_searched_queryset(self):
        search_fields_dict = self.get_search_fields()

        query = self.get_filtered_queryset()
        if not search_fields_dict:
            return query

        for field_name, value in search_fields_dict.items():
            query = query.filter(getattr(self.model_class, field_name).like('%' + value + '%'))
        return query

    def get_ordered_queryset(self):
        query = self.get_searched_queryset()
        for order_filed, desc_or_asc in self.order_by_fields.items():
            if desc_or_asc == 'desc':
                query = query.order_by(-getattr(self.model_class, order_filed))
            else:
                query = query.order_by(getattr(self.model_class, order_filed))
        return query

    def get_context_object_name(self):
        if self.context_object_name:
            return self.context_object_name

        return '{0}_list'.format(self.model_class.__name__.lower())

    def get_page(self):
        try:
            return self.kwargs[self.page_argument]
        except KeyError:
            try:
                return int(request.args[self.page_argument])
            except (KeyError, ValueError):
                return 1

    def get_per_page(self):
        try:
            return self.kwargs[self.per_page_argument]
        except KeyError:
            try:
                return int(request.args[self.per_page_argument])
            except (KeyError, ValueError):
                return CONF.portal.DEFAULT_PER_PAGE or 5

    def get_context_data(self, **kwargs):
        kwargs.update({
            self.get_context_object_name(): self.get_ordered_queryset().paginate(
                page=self.get_page(),
                per_page=self.get_per_page(),
            ),
            'filter_fields_dict': self.get_search_fields(),
            'search': request.args.get('search', '')
        })
        return kwargs


class BaseListView(MultipleObjectMixin, View):

    def get(self, *args, **kwargs):
        return self.render_to_response(self.get_context_data())


class ListView(TemplateResponseMixin, BaseListView):
    pass
