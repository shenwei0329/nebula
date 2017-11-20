# -*- coding: utf-8 -*-
from flask import redirect

from .base import View
from .base import FormMixin
from .base import ProcessFormMixin
from .base import TemplateResponseMixin
from .detail import BaseDetailView
from .detail import SingleObjectMixin


class ModelFormMixin(FormMixin, SingleObjectMixin):

    def get_form_kwargs(self):
        kwargs = super(ModelFormMixin, self).get_form_kwargs()
        kwargs['obj'] = self.object
        return kwargs

    def form_valid(self, form):
        self.populate_obj(form)
        return super(ModelFormMixin, self).form_valid(form)

    def populate_obj(self, form):
        if not self.object:
            self.object = self.model_class()
        form.populate_obj(self.object)
        self.object.save()

    def get_context_data(self, **kwargs):
        context = super(ModelFormMixin, self).get_context_data(**kwargs)
        context.update({
            self.get_context_object_name() : self.object,
        })
        return context


class BaseCreateView(ModelFormMixin, ProcessFormMixin, View):

    def get(self, *args, **kwargs):
        self.object = None
        return super(BaseCreateView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.object = None
        return super(BaseCreateView, self).post(*args, **kwargs)


class CreateView(TemplateResponseMixin, BaseCreateView):
    pass


class BaseUpdateView(ModelFormMixin, ProcessFormMixin, View):

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        return super(BaseUpdateView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        return super(BaseUpdateView, self).post(*args, **kwargs)


class UpdateView(TemplateResponseMixin, BaseUpdateView):
    pass


class DeletionMixin(object):

    success_url = None

    def get_success_url(self):
        return self.success_url

    def delete(self, *args, **kwargs):
        self.object.delete()
        return redirect(self.get_success_url())


class BaseDeleteView(DeletionMixin, BaseDetailView):

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        return super(BaseDeleteView, self).delete(*args, **kwargs)


class DeleteView(TemplateResponseMixin, BaseDeleteView):
    pass
