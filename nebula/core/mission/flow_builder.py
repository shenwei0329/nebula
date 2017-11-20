# -*- coding: utf-8 -*-
import abc
from collections import namedtuple

import six
from taskflow.engines import helpers as engine_helpers
from taskflow.utils import persistence_utils as p_utils

from nebula.core.common import nameutils
from nebula.core.managers import managers
from nebula.core.mission import helpers as flow_helpers
from nebula.mission_control.tasks.flows import execute_job

FlowBuildResult = namedtuple('FlowBuildResult',
                             ['flow', 'flow_detail', 'job', 'resource'])


@six.add_metaclass(abc.ABCMeta)
class Builder(object):
    """A template method object for job/flow creation."""

    def __init__(self, context, resource_args=(), resource_kwargs=None,
                 flow_factory=None, flow_factory_args=(),
                 flow_factory_kwargs=None, store=None):
        """

        :param context: 请求上下文
        :param resource_args: 资源附加参数
        :param resource_kwargs: 资源附加关键字参数
        :param flow_factory: 工厂函数, 用于创建flow (LinearFlow等)
        :param flow_factory_args: 传入工厂函数的参数
        :param flow_factory_kwargs: 传入工厂函数的关键字参数
        :param store: 传入taskflow引擎的附加参数
        """
        if not resource_kwargs:
            resource_kwargs = {}
        if not flow_factory_kwargs:
            flow_factory_kwargs = {}
        if store is None:
            store = {}

        self.context = context
        self.resource_args = resource_args
        self.resource_kwargs = resource_kwargs
        self.flow_factory = flow_factory
        self.flow_factory_args = flow_factory_args
        self.flow_factory_kwargs = flow_factory_kwargs
        self.store = store

    @abc.abstractmethod
    def prepare_resource(self, *args, **kwargs):
        """根据情况, 这里创建资源, 或者返回现有资源"""

    @abc.abstractmethod
    def associate_resource_with_job(self, resource, job):
        """将资源和任务关联起来"""

    def deliver_job(self, job_name, book_uuid, flow_uuid=None):
        store = self.store
        execute_job.delay(job_name, book_uuid, flow_uuid, store=store)

    @staticmethod
    def _get_resource_type(resource):
        return nameutils.snake_casify(resource.__class__.__name__)

    def _create_job(self, resource, logbook, flow_detail):
        resource_type = resource.__class__.__name__
        job = managers.jobs.create(self.context,
                                   resource_id=resource.id,
                                   resource_name=resource.display_name,
                                   resource_type=resource_type,
                                   book_uuid=logbook.uuid,
                                   flow_uuid=flow_detail.uuid,
                                   flow_name=flow_detail.name)
        return job

    def _create_logbook(self, resource, backend):
        user_id = self.context.user_id
        resource_type = self._get_resource_type(resource)
        name = 'book.%(user_id)s.%(resource_type)s' % {
            'user_id': user_id,
            'resource_type': resource_type
        }
        logbook = flow_helpers.create_log_book(
            name, meta=dict(nebula_context=self.context.to_dict()),
            backend=backend)
        return logbook

    def _create_flow_detail(self, flow, logbook, backend):
        flow_detail = p_utils.create_flow_detail(
            flow, book=logbook, backend=backend,
            meta=dict(nebula_context=self.context.to_dict()))
        # In order to safely resume a flow, we need provide a flow factory
        # function, then create that flow on demand
        engine_helpers.save_factory_details(flow_detail,
                                            self.flow_factory,
                                            self.flow_factory_args,
                                            self.flow_factory_kwargs,
                                            backend=backend)
        return flow_detail

    def _inject_store(self, job_name, resource_id, job_id):
        self.store.update({
            '_request_context': self.context.to_dict(),
            'resource_id': resource_id,
            'job_id': job_id,
            'job_name': job_name,
        })

    def build(self, job_name=None):
        resource = self.prepare_resource(*self.resource_args,
                                         **self.resource_kwargs)
        flow = self.flow_factory(*self.flow_factory_args,
                                 **self.flow_factory_kwargs)

        with flow_helpers.get_backend() as backend:
            logbook = self._create_logbook(resource, backend)
            flow_detail = self._create_flow_detail(flow, logbook, backend)

        if job_name is None:
            job_name = flow_detail.name

        job = self._create_job(resource, logbook, flow_detail)
        self.associate_resource_with_job(resource, job)
        self._inject_store(job_name, resource.id, job.id)
        self.deliver_job(job_name, logbook.uuid, flow_detail.uuid)
        return FlowBuildResult(flow=flow, flow_detail=flow_detail, job=job,
                               resource=resource)
