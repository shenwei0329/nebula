# -*- coding: utf-8 -*-
"""
    2015.7.12 by shenwei 增加注释

    建立常用的模板

"""
from oslo_config import cfg

from flask import g
from flask import abort
from flask import render_template
from flask import session
from flask import request
from flask import _app_ctx_stack

from nebula.portal.decorators.auth import require_permission
from nebula.core.views import View
from nebula.core.views import SingleObjectMixin
from nebula.core.views import MultipleObjectMixin
from nebula.core.views import JSONResponseMixin
from nebula.core.views import TemplateResponseMixin
from nebula.core.views import ModelFormMixin
from nebula.core.views import ProcessFormMixin
from nebula.core.views import DeletionMixin
from nebula.portal.utils.menu import DATAMANAGEMENT_MENUS
from nebula.portal.utils.user import User
from nebula.core.views.base import FormMixin

CONF = cfg.CONF
CONF.import_group('portal', 'nebula.portal.options')

class InjectedMenu():

    def get_context_data(self, **additional_context):
        context = {}
        context.update({
            'datamng_menus': self.datamng_menus,
            'main_menus_mini': self.main_menus_mini,
            'show_profile': self.show_profile,
            'user': session['user'],
        })
        context.update(additional_context)
        return context

class InjectedMultipleObjectMixin(MultipleObjectMixin):

    def get_context_data(self, **additional_context):
        context = super(InjectedMultipleObjectMixin,
                        self).get_context_data(**additional_context)
        context.update({
            'datamng_menus': self.datamng_menus,
            'main_menus_mini': self.main_menus_mini,
            'show_profile': self.show_profile,
            'user': session['user'],
        })
        context.update(additional_context)
        return context


class InjectedModelFormMixin(ModelFormMixin):

    def get_context_data(self, **additional_context):
        context = super(InjectedModelFormMixin,
                        self).get_context_data(**additional_context)
        context.update({
            'datamng_menus': self.datamng_menus,
            'main_menus_mini': self.main_menus_mini,
            'show_profile': self.show_profile,
            'user': session['user'],
        })
        context.update(additional_context)
        return context


class InjectedSingleObjectMixin(SingleObjectMixin):

    def get_context_data(self, **additional_context):
        context = super(InjectedSingleObjectMixin,
                        self).get_context_data(**additional_context)
        context.update({
            'datamng_menus': self.datamng_menus,
            'main_menus_mini': self.main_menus_mini,
            'show_profile': self.show_profile,
            'user': session['user'],
        })
        context.update(additional_context)
        return context

######################################################################
# Builder Mixins
######################################################################
class BuilderMixin(object):

    builder_class = None

    def get_builder_class(self, resource_kwargs):
        return self.builder_class

    def get_builder_result(self, resource_kwargs=None):
        builder = self.get_builder_class(resource_kwargs)(self.context, resource_kwargs=resource_kwargs)
        rv = builder.build()
        return {
            'job': {
                'id': rv.job.id,
                'state': rv.job.state,
                'display_desc': rv.job.display_desc,
            },
            'resource': {
                'id': rv.resource.id,
                'name': hasattr(rv, 'display_name') and rv.resource.display_name or '',
                'type': rv.resource.__class__.__name__.lower(),
            },
        }


class BuilderFormMixin(object):

    def form_invalid(self, form):
        return self.render_to_response(context_data={'errors': form.errors})

    def form_valid(self, form):
        return self.render_to_response(context_data=self.get_builder_result(form.data))


######################################################################
# Base Views
######################################################################
class BaseView(View):

    active_module = None

    def __init__(self):
        self.datamng_menus = DATAMANAGEMENT_MENUS
        self.main_menus_mini = False
        self.show_profile = False

    def dispatch_request(self, *args, **kwargs):
        return super(BaseView, self).dispatch_request(*args, **kwargs)

    def render_template(self, template_name_or_list, **additional_context):
        """Helper method to render templates, impart with context."""
        context = {
            'show_profile': self.show_profile,
        }
        context.update(additional_context)
        return render_template(template_name_or_list, **context)

    def get_context_data(self, **kwargs):
        context = dict()
        context.update(kwargs)
        return context

    def get_form_kwargs(self):
        """
        更新URL中的占位符参数到Form data中.
        """
        kwargs = super(BaseView, self).get_form_kwargs()
        kwargs.update(self.kwargs)
        return kwargs


class AuthorizedView(BaseView):
    decorators = (require_permission,)


class FormView(FormMixin, ProcessFormMixin, TemplateResponseMixin, AuthorizedView):
    pass


class JsonView(JSONResponseMixin, AuthorizedView):
    """
    Json Render View
    """
    def get(self, *args, **kwargs):
        return self.render_to_response(self.get_context_data())


######################################################################
# List Views
######################################################################
class BaseListView(InjectedMultipleObjectMixin, AuthorizedView):

    user_only = False # 如果为True, 管理员也只能查看属于自己的数据

    def get(self, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def get_queryset(self):
        """
        普通用户只能查询属于自己的记录, 管理员能查询所有记录
        """
        query = super(BaseListView, self).get_queryset()
        if not self.context.is_super or self.user_only:
            if hasattr(self.model_class, 'owner_id'):
                query = query.filter_by(owner_id=self.context.user_id)
        return query


class ListView(TemplateResponseMixin, BaseListView):
    """
    基础模板列表通用视图. 返回模板渲染HTML

    继承此通用视图, 需要覆写如下属性与方法::

        class VirtualrouterListView(ListView):
            active_module = 'network'
            model_class = Virtualrouter
            template_name = 'network/virtualrouters.html'
            search_fields = {
                'name': 'search'
            }
    """
    context_object_name = 'pagination'

    def get_context_data(self, **additional_context):
        context = super(ListView, self).get_context_data(**additional_context)

        if hasattr(self, 'model_class'):
            context.update({
                'resource_type': self.model_class.__name__,
            })
        if request.args.get('resource_id'):
            context.update({
                'resource_id': request.args.get('resource_id'),
            })
        return context



class JsonListView(JSONResponseMixin, BaseListView):
    """
    基础模板列表通用视图. 返回JSON

    继承此通用视图, 需要覆写如下属性与方法::

        class VirtualrouterListView(ListView):
            active_module = 'network'
            model_class = Virtualrouter
            list_feilds = ['id', 'name'] # 使用list_feilds列表中包含的key, 过滤返回的json字典. 如果list_feilds为空, 则不进行任何操作.
            search_fields = {
                'name': 'search'
            }
    """
    # 使用list_feilds列表中包含的key, 过滤返回的json字典. 如果list_feilds为空, 则不进行任何操作.
    list_feilds = []

    def get_context_data(self, **additional_context):
        return {self.get_context_object_name(): [
            self._filter_by_list_feilds(obj.to_dict())
            for obj in self.get_ordered_queryset()
        ]}

    def _filter_by_list_feilds(self, obj_dict):
        if self.list_feilds:
            result_dict = {}
            for key, value in obj_dict.items():
                if key in self.list_feilds:
                    result_dict.update({key:value})
            return result_dict
        return obj_dict



######################################################################
# Create Views
######################################################################
class BaseCreateView(InjectedModelFormMixin, ProcessFormMixin, AuthorizedView):

    def get(self, *args, **kwargs):
        self.object = None
        return super(BaseCreateView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.object = None
        return super(BaseCreateView, self).post(*args, **kwargs)


class CreateView(TemplateResponseMixin, BaseCreateView):
    """
    基础模板创建通用视图. 返回结果基于URL跳转.
    """
    pass


class JsonCreateView(JSONResponseMixin, BaseCreateView):
    """
    基础JSON创建通用视图. 返回JSON RESPONSE.

    继承此通用视图, 需要覆写如下属性与方法::

        class PublicIPCreateView(JsonCreateView):

            form_class = PublicIPCreateForm     # 验证Form
            model_class = VirtualrouterPublicIP # Model

            def populate_obj(self, form):
                self.object = managers.virtualrouter_publicips.create(
                    context=self.context,
                    public_ip=form.public_ip.data,
                    creator_id=self.context.user_id,
                    owner_id=form.owner_id.data,
                )
    """

    def form_invalid(self, form):
        return self.render_to_response(context_data={'errors': form.errors})

    def form_valid(self, form):
        self.populate_obj(form)
        return self.render_to_response(context_data=self.get_context_data())

    def get_context_data(self, **additional_context):
        return {
            self.get_context_object_name(): self.object.to_dict()
        }


class BuilderCreateView(BuilderMixin,
                        BuilderFormMixin,
                        JSONResponseMixin,
                        BaseCreateView):
    """
    基础Builder创建通用视图, 返回JSON RESPONSE. 用于后台Task任务创建.

    继承此通用视图, 需要覆写如下属性与方法::

        class VirtualrouterCreateView(BuilderCreateView):

            form_class = VirtualRouterCreateForm
            builder_class = VirtualrouterCreateBuilder
    """
    pass



######################################################################
# Update Views
######################################################################
class BaseUpdateView(InjectedModelFormMixin, ProcessFormMixin, AuthorizedView):

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        return super(BaseUpdateView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.object = None
        return super(BaseUpdateView, self).post(*args, **kwargs)


class UpdateView(TemplateResponseMixin, BaseUpdateView):
    pass


class BuilderUpdateView(BuilderMixin, BuilderFormMixin,
                        JSONResponseMixin, BaseUpdateView):

    def get_builder_result(self, resource_kwargs=None):
        if self.kwargs.get is not None:
            resource_kwargs.update({
                'resource_id': self.kwargs[self.pk_field]
            })
        return super(BuilderUpdateView, self).get_builder_result(resource_kwargs)


######################################################################
# Detail Views
######################################################################
class BaseDetailView(InjectedSingleObjectMixin, AuthorizedView):

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data())

    def get_object(self):
        object = super(BaseDetailView, self).get_object()
        # 非管理员不能查看不属于自己的资源
        if not self.context.is_super and \
                hasattr(object, 'owner_id') and \
                object.owner_id != self.context.user_id:
            abort(404)
        return object


class DetailView(TemplateResponseMixin, BaseDetailView):

    def get_context_data(self, **additional_context):
        context = super(DetailView, self).get_context_data(**additional_context)

        if hasattr(self, 'model_class'):
            context.update({
                'resource_type': self.model_class.__name__,
            })
        context.update({'resource_id': self.object.id})
        return context


######################################################################
# Delete Views
######################################################################
class BaseDeleteView(DeletionMixin, BaseDetailView):

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        return super(BaseDeleteView, self).delete(*args, **kwargs)


class DeleteView(TemplateResponseMixin, BaseDeleteView):
    pass


class BuilderDeleteView(BuilderMixin, JSONResponseMixin, BaseDetailView):

    # def delete(self, *args, **kwargs):
    #     return self.render_to_response(context_data=self.get_builder_result({
    #         'resource_id': kwargs[self.pk_field]
    #     }))

    def delete(self, *args, **kwargs):
        if kwargs.get(self.pk_field):
            return self.render_to_response(context_data=self.get_builder_result({
                'resource_id': kwargs[self.pk_field]
            }))

        ids = [i for i in kwargs["ids"].split(",") if i]
        context_data = map(lambda x:
                           self.get_builder_result({'resource_id': x}), ids)
        return self.render_to_response(context_data=context_data)


