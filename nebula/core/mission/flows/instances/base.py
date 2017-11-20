# -*- coding: utf-8 -*-
import logging

from nebula.core.managers import managers
from nebula.core.mission import flow_builder

LOG = logging.getLogger(__name__)


class InstanceURDBuilder(flow_builder.Builder):
    def __init__(self, context, flow_factory, resource_kwargs=None, store=None):
        super(InstanceURDBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=flow_factory,
            store=store)

    def associate_resource_with_job(self, resource, job):
        managers.instances.update(self.context, resource.id, dict(job_id=job.id))

    def prepare_resource(self, *args, **kwargs):
        LOG.info("(****************************************************)")
        LOG.info(kwargs)
        instance_obj = managers.instances.get(self.context, kwargs['resource_id'])
        self.store.update({'instance_uuid': instance_obj.instance_uuid})
        self.store.update(kwargs)
        return instance_obj


