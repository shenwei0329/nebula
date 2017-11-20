# Copyright 2010 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Possible vm states for instances.

Compute instance vm states represent the state of an instance as it pertains to
a user or administrator.

vm_state describes a VM's current stable (not transition) state. That is, if
there is no ongoing compute API calls (running tasks), vm_state should reflect
what the customer expect the VM to be. When combined with task states
(task_states.py), a better picture can be formed regarding the instance's
health and progress.

See http://wiki.openstack.org/VMState
"""
from nebula.core.i18n import _

ACTIVE = 'active'  # VM is running
ACTIVE_ = 'active_' # VM is running, set by nebula for reboot status.
BUILDING = 'building'  # VM only exists in DB
REBOOTING = 'rebooting' # VM is rebooting
PAUSED = 'paused'
SUSPENDED = 'suspended'  # VM is suspended to disk.
STOPPED = 'stopped'  # VM is powered off, the disk image is still there.
RESCUED = 'rescued'  # A rescue image is running with the original VM image
# attached.
RESIZED = 'resized'  # a VM with the new size is active. The user is expected
# to manually confirm or revert.
BACKUP_DISK = 'backup_disk'  # VM is backuping disk
MIGRATE = 'migrating' #VM is migrating from one host to another host

SOFT_DELETED = 'soft-delete'  # VM is marked as deleted but the disk images are
# still available to restore.
DELETED = 'deleted'  # VM is permanently deleted.

ERROR = 'error'

SHELVED = 'shelved'  # VM is powered off, resources still on hypervisor
SHELVED_OFFLOADED = 'shelved_offloaded'  # VM and associated resources are
# not on hypervisor

# states we allow hard reboot from
RESTORE_TO_HOST = 'restore-to-host'

ALLOW_SOFT_REBOOT = [ACTIVE]  # states we can soft reboot from
ALLOW_HARD_REBOOT = ALLOW_SOFT_REBOOT + [STOPPED, PAUSED, SUSPENDED, ERROR]
ALLOW_START = [STOPPED]
ALLOW_SHUTDOWN = [ACTIVE]
ALLOW_RENAME = [ACTIVE]
ALLOW_RESIZE = [ACTIVE]
ALLOW_PAUSE = [ACTIVE]
ALLOW_UNPAUSE = [PAUSED]
ALLOW_SUSPEND = [ACTIVE]
ALLOW_RESUME = [SUSPENDED]
ALLOW_BACKUP = [ACTIVE]
ALLOW_CHANGE_PASSWD = [STOPPED]
ALLOW_CHANGE_IOPS = [ACTIVE]
ALLOW_ATTACH_VOLUME = [ACTIVE] + [STOPPED]

# Openstack Client Actions
ACTIONS = (
    _('start'),
    _('change'),
    _('modify'),
    _('pause'),
    _('reboot'),
    _('resume'),
    _('shutdown'),
    _('suspend'),
    _('unsuspend'),
    _('unpause'),
    _('backup'),
    _('change_admin_password'),
    _('change_iops'),
)

ALLOW_ACTION_MAP = {
    'start': ALLOW_START,
    'change': ALLOW_RENAME,
    'modify': ALLOW_RESIZE,
    'pause': ALLOW_PAUSE,
    'reboot': ALLOW_HARD_REBOOT,
    'resume': ALLOW_RESUME,
    'shutdown': ALLOW_SHUTDOWN,
    'suspend': ALLOW_SUSPEND,
    'unsuspend': ALLOW_RESUME,
    'unpause': ALLOW_UNPAUSE,
    'backup': ALLOW_BACKUP,
    'change_admin_password': ALLOW_CHANGE_PASSWD,
    'change_iops': ALLOW_CHANGE_IOPS,
}
