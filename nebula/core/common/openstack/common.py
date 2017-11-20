# -*- coding: utf-8 -*-
import six

from nebula.openstack.common import log as logging
from nebula.core.i18n import _

from . import task_states
from . import vm_states

LOG = logging.getLogger(__name__)

_ACTIVE_MAP = {
    'default': 'ACTIVE',
    task_states.REBOOTING: 'REBOOT',
    task_states.REBOOT_PENDING: 'REBOOT',
    task_states.REBOOT_STARTED: 'REBOOT',
    task_states.REBOOTING_HARD: 'HARD_REBOOT',
    task_states.REBOOT_PENDING_HARD: 'HARD_REBOOT',
    task_states.REBOOT_STARTED_HARD: 'HARD_REBOOT',
    task_states.UPDATING_PASSWORD: 'PASSWORD',
    task_states.REBUILDING: 'REBUILD',
    task_states.REBUILD_BLOCK_DEVICE_MAPPING: 'REBUILD',
    task_states.REBUILD_SPAWNING: 'REBUILD',
    task_states.MIGRATING: 'MIGRATING',
    task_states.RESIZE_PREP: 'RESIZE',
    task_states.RESIZE_MIGRATING: 'RESIZE',
    task_states.RESIZE_MIGRATED: 'RESIZE',
    task_states.RESIZE_FINISH: 'RESIZE',
    task_states.BACKUP_DISK: 'BACKUP_DISK',
    }


_STATE_MAP = {
    vm_states.ACTIVE: _ACTIVE_MAP,
    vm_states.ACTIVE_: _ACTIVE_MAP,
    vm_states.BUILDING: {
        'default': 'BUILD',
    },
    vm_states.REBOOTING: { # 计算组新增状态, 标识虚拟机在重启过程中.
        'default': 'REBOOT',
    },
    vm_states.STOPPED: {
        'default': 'SHUTOFF',
        task_states.RESIZE_PREP: 'RESIZE',
        task_states.RESIZE_MIGRATING: 'RESIZE',
        task_states.RESIZE_MIGRATED: 'RESIZE',
        task_states.RESIZE_FINISH: 'RESIZE',
    },
    vm_states.RESIZED: {
        'default': 'VERIFY_RESIZE',
        # Note(maoy): the OS API spec 1.1 doesn't have CONFIRMING_RESIZE
        # state so we comment that out for future reference only.
        #task_states.RESIZE_CONFIRMING: 'CONFIRMING_RESIZE',
        task_states.RESIZE_REVERTING: 'REVERT_RESIZE',
    },
    vm_states.PAUSED: {
        'default': 'PAUSED',
    },
    vm_states.SUSPENDED: {
        'default': 'SUSPENDED',
    },
    vm_states.RESCUED: {
        'default': 'RESCUE',
    },
    vm_states.ERROR: {
        'default': 'ERROR',
    },
    vm_states.DELETED: {
        'default': 'DELETED',
    },
    vm_states.SOFT_DELETED: {
        'default': 'SOFT_DELETED',
    },
    vm_states.SHELVED: {
        'default': 'SHELVED',
    },
    vm_states.SHELVED_OFFLOADED: {
        'default': 'SHELVED_OFFLOADED',
    },
    vm_states.BACKUP_DISK: {
        'default': 'BACKUP_DISK',
    },
}


def status_from_state(vm_state, task_state='default'):
    """Given vm_state and task_state, return a status string."""
    task_map = _STATE_MAP.get(vm_state, dict(default='UNKNOWN'))
    status = task_map.get(task_state, task_map['default'])
    if status == "UNKNOWN":
        LOG.error(_("status is UNKNOWN from vm_state=%(vm_state)s "
                    "task_state=%(task_state)s. Bad upgrade or db "
                    "corrupted?"),
                  {'vm_state': vm_state, 'task_state': task_state})
    return status


def task_and_vm_state_from_status(status):
    """Map the server status string to list of vm states and
    list of task states.
    """
    vm_states = set()
    task_states = set()
    for state, task_map in six.iteritems(_STATE_MAP):
        for task_state, mapped_state in six.iteritems(task_map):
            status_string = mapped_state
            if status.lower() == status_string.lower():
                vm_states.add(state)
                task_states.add(task_state)
    # Add sort to avoid different order on set in Python 3
    return sorted(vm_states), sorted(task_states)
