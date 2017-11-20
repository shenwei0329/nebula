# -*- coding: utf-8 -*-
from flask import abort

from .base import View, TemplateResponseMixin


class SingleObjectMixin(object):
    model_class = None

    pk_field = 'id'

    context_object_name = None

    def get_context_object_name(self):
        if self.context_object_name:
            return self.context_object_name

        return self.model_class.__name__.lower()

    def get_queryset(self):
        return self.model_class.query

    def get_object(self):
        return self.get_queryset().get_or_404(self.kwargs[self.pk_field])

    def get_context_data(self, **kwargs):
        kwargs[self.get_context_object_name()] = self.object
        return kwargs


class BaseDetailView(SingleObjectMixin, View):

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data())


class DetailView(TemplateResponseMixin, BaseDetailView):
    pass
