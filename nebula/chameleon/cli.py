# -*- coding: utf-8 -*-
import eventlet  # isort:skip
eventlet.monkey_patch(socket=True, select=True, thread=True)

from nebula.chameleon import notification
from nebula.chameleon import service
from nebula.chameleon.central import manager as central_manager
from nebula.openstack.common import service as os_service


def agent_notification():
    service.prepare_service('nebula-chameleon')
    launcher = os_service.ProcessLauncher()
    launcher.launch_service(
        notification.NotificationService(),
        workers=service.get_workers('notification'))
    launcher.wait()


def agent_central():
    service.prepare_service('nebula-chameleon')
    os_service.launch(central_manager.AgentManager()).wait()
