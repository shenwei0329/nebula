# -*- coding: utf-8 -*-
import re
from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients.nova import get_client as get_nova_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = 'aggregate:delete'


class DeleteAggregateTask(task.NebulaTask):

    default_provides = 'callapi'

    def __init__(self):
        super(DeleteAggregateTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, resource_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始删除集群"))
        resource = managers.aggregates.get(self.admin_context, resource_id)

        self.update_job_state_desc(job_id, _(u"开始删除资源"))
        LOG.info("DeleteAggregateTask_1::::::::")
        LOG.info(resource.aggregate_uuid)
        if not resource.aggregate_uuid:
            managers.aggregates.delete(resource_id)
            self.update_job_state_desc(job_id, _(u"删除集群成功"))
            return

        try:
            rv = get_nova_client().servers.delete_aggregate(
                resource.aggregate_uuid
            )
        except Exception as err:
            error = str(err)
            if re.search(r'[\w|-]{36}|None\sdoes not exist', error):
                #self.update_job_state_desc(job_id, _(u"虚拟路由器已经被删除，可以忽略！"))
                pass
            elif re.search(r'[\w|-]{36}|could not be found', error):
                pass
            else:
                self.update_job_state_desc(job_id, _(error))
                raise err

        self.update_job_state_desc(job_id, _(u"删除资源成功"))

        self.update_job_state_desc(job_id, _(u"开始删除数据库记录"))
        LOG.error("resource_id: " + str(resource_id))
        managers.aggregates.delete(resource_id)
        self.update_job_state_desc(job_id, _(u"删除集群成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"删除集群失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DeleteAggregateTask())
    return flow


class AggregateDeleteBuilder(Builder):

    def __init__(self, context=None, resource_kwargs=None, **kwargs):
        super(AggregateDeleteBuilder, self).__init__(
            context=context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            **kwargs
        )

    def prepare_resource(self, *args, **kwargs):
        return managers.aggregates.get(self.context, kwargs['resource_id'])

    def associate_resource_with_job(self, resource, job):
        pass
