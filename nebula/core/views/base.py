# -*- coding: utf-8 -*-
from flask import current_app, request
from flask import redirect, g
from flask import render_template
from flask.views import MethodView
from oslo_config import cfg

CONF = cfg.CONF
CONF.import_group('portal', 'nebula.portal.options')


class View(MethodView):

    def dispatch_request(self, *args, **kwargs):
        self.args = g.request_args = args
        self.kwargs = g.request_kwargs = kwargs
        return super(View, self).dispatch_request(*args, **kwargs)

class TemplateResponseMixin(object):
    template_name = None

    def get_template_name(self):
        return self.template_name

    def render_to_response(self, context_data={}):
        return render_template(self.get_template_name(), **context_data)


class TemplateView(TemplateResponseMixin, View):

    def get_context_data(self, **context):
        return context

    def get(self, *args, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))


class FormMixin(object):

    form_class = None
    initial = {}
    success_url = None

    def get_initial(self):
        return self.initial

    def get_success_url(self):
        return self.success_url

    def get_context_data(self, **kwargs):
        return kwargs

    def get_form_kwargs(self):
        # kwargs = {'formdata': request.form}
        kwargs = {}
        kwargs.update(self.get_initial())
        return kwargs

    def get_form(self):
        return self.form_class(**self.get_form_kwargs())
        # return self.form_class()

    def form_valid(self, form):
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ProcessFormMixin(object):
    methods = ['GET', 'POST']

    def get(self, *args, **kwargs):
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, *args, **kwargs):
        form = self.get_form()
        if form.validate():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class BaseFormView(FormMixin, ProcessFormMixin, View):
    pass


class FormView(TemplateResponseMixin, BaseFormView):
    pass


class JSONResponseMixin(object):
    def render_to_response(self, context_data=None):
        if context_data is None:
            context_data = {}
        indent = None
        if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] \
                and not request.is_xhr:
            indent = 2
        return current_app.response_class(
            jsonutils.dumps(context_data, indent=indent, ensure_ascii=False),
            mimetype='application/json'
        )


class JSONView(JSONResponseMixin, View):

    def get_context_data(self, **kwargs):
        return kwargs

    def get(self, *args, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))
