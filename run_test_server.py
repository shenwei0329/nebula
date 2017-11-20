#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
from oslo_config import cfg

import nebula.portal.app
from nebula.core.common.greetingutils import print_greeting

CONF = cfg.CONF

if __name__ == '__main__':
    print_greeting()
    app = nebula.portal.app.create_app()
    app.run(host=CONF.portal.address, port=CONF.portal.port)
