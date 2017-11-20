#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gevent
import gevent.monkey
gevent.monkey.patch_all()

from gevent.pywsgi import WSGIServer

from oslo_config import cfg

from nebula.portal.app import create_app
from nebula.core.common.greetingutils import print_greeting

CONF = cfg.CONF
CONF.import_group('portal', 'nebula.portal.options')

if __name__ == '__main__':
    print_greeting()
    app = create_app()
    http_server = WSGIServer(CONF.portal.address, CONF.portal.port, app)
    http_server.serve_forever()
