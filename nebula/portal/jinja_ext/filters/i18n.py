# coding=utf-8
from nebula.core.i18n import _


QUOTA_NAMES = [
    _('instances'),
    _('cores'),
    _('ram'),
    _('images'),
    _('floating_ips'),
    _('fixed_ips'),
    _('metadata_items'),
    _('injected_files'),
    _('injected_file_content_bytes'),
    _('injected_file_path_length'),
    _('instance_attach_volumes'),
    _('instance_attach_ports'),
    _('instance_backups'),
    _('volume_backups'),
    _('volume_capacity'),
    _('instance_cores_min'),
    _('instance_cores_max'),
    _('instance_ram_min'),
    _('instance_ram_max'),
    _('network_vlan_min'),
    _('network_vlan_max'),
    _('virtual_routers'),
    _('firewalls'),
    _('bandwidth_tx'),
    _('bandwidth_rx'),
    _('binding_publicips'),
    _('private_networks'),
    _('volumes'),
    _('binding_private_networks'),
    _('attach_ports'),
    _('instance_attach_volumes'),
    _('volume_backups'),
    _('system_cores'),
    _('system_ram'),
    _('system_local_storage'),
]


def gettext(text):
    return _(text)
