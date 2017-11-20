# Copyright (c) 2012 OpenStack Foundation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

# Default paths
CORE_PATH = os.path.dirname(__file__)
CODE_PATH = os.path.dirname(os.path.dirname(CORE_PATH))
RELATIVE_LOCALE_PATH = 'nebula/locale'
LOCALE_PATH = os.path.join(CODE_PATH, RELATIVE_LOCALE_PATH)
UPLOAD_IMG_FILE_PATH = os.path.join(CODE_PATH, 'etc/data/_img_upload_tmp')
STATIC_LOGO_PATH = '/static/upload/logo'
UPLOAD_SYSTEM_LOGO_FILE_PATH = os.path.join(CODE_PATH, 'nebula/portal%s' % STATIC_LOGO_PATH)

# Default Config File
DEFAULT_CONFIG_FILE = 'etc/nebula/nebula.conf'
# Default Config ENV
DEFAULT_CONFIG_ENVVAR = 'NEBULA_CONFIG_FILE'

# Default i18n
DEFAULT_LOCALE = 'zh'
DEFAULT_TIMEZONE = 'Asia/Shanghai'

# TODO(salv-orlando): Verify if a single set of operational
# status constants is achievable
NET_TYPE_VLAN = 'vlan'
NET_TYPE_GRE = 'gre'
NET_TYPE_FLAT = 'flat'
NET_TYPE_VXLAN = 'vxlan'

NET_STATUS_ACTIVE = 'ACTIVE'
NET_STATUS_BUILD = 'BUILD'
NET_STATUS_DOWN = 'DOWN'
NET_STATUS_ERROR = 'ERROR'

PORT_STATUS_ACTIVE = 'ACTIVE'
PORT_STATUS_BUILD = 'BUILD'
PORT_STATUS_DOWN = 'DOWN'
PORT_STATUS_ERROR = 'ERROR'

IPv4 = '4'
IPv6 = '6'

SECURITY_GROUP_RULE_DIRECTION_INGRESS = 'ingress'
SECURITY_GROUP_RULE_DIRECTION_EGRESS = 'egress'

NET_PROTOCOL_HTTP = "http"
NET_PROTOCOL_HTTPS = "https"
NET_PROTOCOL_TCP = "tcp"
NET_PROTOCOL_UDP = "udp"
NET_PROTOCOL_ICMP = "icmp"
NET_PROTOCOL_IP = "ip"


LB_METHOD_ROUND_ROBIN = "ROUND_ROBIN"
LB_METHOD_LEAST_CONNECTION = "LEAST_CONNECTIONS"
LB_METHOD_ROUND_SOURCE_IP = "SOURCE_IP"


VOLUME_CREATING = "creating"
VOLUME_AVAILABLE = "available"
VOLUME_IN_USE = "in-use"
VOLUME_DELETING = "deleting"
VOLUME_DELETED = "deleted"
VOLUME_ERROR = "error"
VOLUME_BACKUPING = "backuping"
VOLUME_EXTENDING = "extending"
VOLUME_ATTACHING = "attaching"
VOLUME_DETACHING = "detaching"

VOLUME_TYPE_GLUSTERFS = "gluster"
VOLUME_TYPE_VMWARE = "vmware"
VOLUME_TYPE_LVM = "lvm"
VOLUME_TYPE_NFS = "nfs"
VOLUME_TYPE_CEPH = "ceph"
VOLUME_TYPE_HYPERV = "hyperv"
VOLUME_TYPE_ALL = [VOLUME_TYPE_GLUSTERFS,VOLUME_TYPE_VMWARE,
                   VOLUME_TYPE_LVM,VOLUME_TYPE_NFS,
                   VOLUME_TYPE_CEPH,VOLUME_TYPE_HYPERV]
 
IMAGE_STATUS_QUEUED = 'queued'
IMAGE_STATUS_SAVING = 'saving'
IMAGE_STATUS_ACTIVE = 'active'
IMAGE_STATUS_KILLED = 'killed'
IMAGE_STATUS_DELETED = 'deleted'
IMAGE_STATUS_PENDING_DELETE = 'pending_delete'
IMAGE_STATUS_ERROR = 'error'
IMAGE_STATUS_ALL = [IMAGE_STATUS_QUEUED, IMAGE_STATUS_SAVING,
                    IMAGE_STATUS_ACTIVE, IMAGE_STATUS_KILLED,
                    IMAGE_STATUS_DELETED, IMAGE_STATUS_PENDING_DELETE,
                    IMAGE_STATUS_ERROR]


JOB_STATUS_SUCCESS = 'SUCCESS'
JOB_STATUS_FAILURE = 'FAILURE'
JOB_STATUS_REVERTED = 'REVERTED'
JOB_STATUS_PENDING = 'PENDING'
JOB_STATUS_RUNNING = 'RUNNING'

JOB_STATUS_SUCCESS_LIST = (
    JOB_STATUS_SUCCESS,
)
JOB_STATUS_FAILURE_LIST = (
    JOB_STATUS_FAILURE,
    JOB_STATUS_REVERTED,
)
JOB_STATUS_RUNNING_LIST = (
    JOB_STATUS_RUNNING,
)
JOB_STATUS_PENDING_LIST = (
    JOB_STATUS_PENDING,
)

HOST_STATUS_ADDING = "adding"
HOST_STATUS_ACTIVE = "active"
HOST_STATUS_ERROR = "error"
HOST_STATUS_MAINTAIN = "maintenance"

HOST_STATE_UP = "up"
HOST_STATE_DOWN = "down"
HOST_STATE_ALL = [HOST_STATE_UP, HOST_STATE_DOWN]

ALARM_METER_TYPE_HOST = '1'
ALARM_METER_TYPE_VM = '2'
ALARM_METER_TYPE_ALL = [ALARM_METER_TYPE_HOST, ALARM_METER_TYPE_VM]


QUOTA_USER_LEVEL = [
    'instances',
    'cores',
    'ram'
]

QUOTA_SYSTEM_LEVEL = [
    'instance_attach_ports'
    'instance_attach_volumes',
    'instance_backups',
    'volume_backups',
    'binding_private_networks',
    'attach_ports',
    'system_cores',
    'system_ram',
    'system_local_storage',
]

YES = "yes"
NO = "no"
