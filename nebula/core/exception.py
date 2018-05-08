# -*- coding: utf-8 -*-

import sys
import logging


LOG = logging.getLogger(__name__)


class NebulaException(Exception):

    msg_fmt = "An unknown exception occurred."
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs
            except Exception as ex:
                LOG.error(ex)
                exc_info = sys.exc_info()
                LOG.exception('Exception in string format operation')
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))
        super(NebulaException, self).__init__(message)

    def format_message(self):
        return self.args[0]

