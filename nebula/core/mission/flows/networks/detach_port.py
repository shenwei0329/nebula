# -*- coding: utf-8 -*-
import re
from taskflow.patterns import linear_flow

from nebula.core.managers import managers
from nebula.core.mission import task
from nebula.core.mission.flow_builder import Builder
from nebula.core.openstack_clients. \
    nova import get_client as get_nova_client
from nebula.openstack.common import log
from nebula.core.i18n import _

LOG = log.getLogger(__name__)
ACTION = "port:detach"


class DetachPortTask(task.NebulaTask):

    default_provides = 'port'

    def __init__(self):
        super(DetachPortTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, port_id, **kwargs):
        self.update_job_state_desc(job_id, _(u"开始卸载网卡"))
        resource = managers.ports.get(self.admin_context, port_id)
        try:
            get_nova_client().servers.interface_detach(
                resource.instance.instance_uuid,
                resource.port_uuid
            )
        except Exception as err:
            error = str(err)
            self.update_job_state_desc(job_id, _(error))
            if re.search(r'[\w|-]{36}|None\sdoes not exist', error) or resource.port_uuid:
                self.update_job_state_desc(job_id, _(u"网卡已经被卸载"))
                pass
            else:
                raise err
        self.update_job_state_desc(job_id, _(u"卸载网卡成功"))

    def revert(self, job_id, *args, **kwargs):
        self.update_job_state_desc(job_id, _(u"卸载网卡失败"))


class DeletePortEntryTask(task.NebulaTask):

    def execute(self, job_id, port_id, **kwargs):
        # 删除数据库中私有网络
        self.update_job_state_desc(job_id, _(u"开始删除网卡"))
        managers.ports.delete(port_id)
        self.update_job_state_desc(job_id, _(u"网卡断开虚拟机成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"网卡断开虚拟机失败"))


def get_delete_port_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(DetachPortTask(),
             DeletePortEntryTask())
    return flow


class PortDetachBuilder(Builder):

    def __init__(self, context, resource_args=(), resource_kwargs=None):
        super(PortDetachBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_delete_port_flow,
        )

    def prepare_resource(self, *args, **kwargs):
        self.store.update(kwargs)
        port = managers.ports.get(self.context, kwargs["port_id"])
        if kwargs.get('instance_id'):
            return port.instance
        else:
            return port.network

    def associate_resource_with_job(self, resource, job):
        if self.store.get("instance_id"):
            managers.instances.update(self.context,
                                      resource.id, dict(job_id=job.id))
        else:
            managers.private_networks.update(self.context, resource.id, job_id=job.id)

