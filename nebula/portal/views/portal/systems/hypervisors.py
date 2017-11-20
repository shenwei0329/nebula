# -*- coding: utf-8 -*-
import logging
from nebula.portal.views.base import AuthorizedView
from .base import SystemMixin
from nebula.core.openstack_clients import nova
from nebula.core.managers import managers

LOG = logging.getLogger(__name__)


class ActiveMixin(object):
    active_module = 'hypervisors'

class HypervisorView(SystemMixin, ActiveMixin, AuthorizedView):
    template_name = 'systems/system_hypervisors.html'
    hypervisors = []

    def get_context_data(self, **kwargs):
        context = super(HypervisorView, self).get_context_data(**kwargs)
        try:
            self.hypervisors = nova.get_client().hypervisors.list()
        except Exception as e:
            LOG.error("Openstack service is not available [nova.get_client().hypervisors.list()]")
            LOG.error(e)

        context.update(dict(
            hypervisors=self.hypervisors,
            resources=self._get_statistics()
        ))
        return context

    def get(self, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_template(self.template_name, **context)

    def _get_statistics(self):
        return dict(
            floating_ips=managers.virtualrouter_floatingips.stat_all(),
            cores=self._get_cores_stat(),
            ram=self._get_ram_stat(),
            disk=self._get_disk_stat(),
        )

    def _get_cores_stat(self):
        total_cores = self._total("vcpus")
        usages = managers.instances.sum_cores()
        data = dict(
            total=total_cores,
            usages=usages
        )
        return data

    def _get_ram_stat(self):
        total = self._total("ram")
        usages = managers.instances.sum_ram()
        data = dict(
            total=total,
            usages=usages
        )
        return data

    def _get_disk_stat(self):
        instance_disk = managers.instances.sum_disk()
        volumes_disk = managers.volumes.count_all_size()
        instance_backup_disk = managers.instance_backups.sum_disk()
        usages = instance_disk + volumes_disk + \
                 int(float(instance_backup_disk) / 1024 / 1024 / 1024)
        data = dict(
            total=self._total("disk"),
            usages=usages,
        )
        return data
    def _total(self, type):
        if type == "vcpus":
            return sum([hyper.vcpus or 0 for hyper in self.hypervisors])
        elif type == "ram":
            return sum([hyper.memory_mb or 0 for hyper in self.hypervisors])
        elif type == "disk":
            return sum([hyper.local_gb or 0 for hyper in self.hypervisors])
        else:
            return 0