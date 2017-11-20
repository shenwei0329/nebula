# -*- coding: utf-8 -*-
import logging


class JobContextAdapter(logging.LoggerAdapter):
    def __init__(self, logger, job_name, book_uuid, flow_uuid):
        self.logger = logger
        self.extra = {
            'job_name': job_name,
            'book_uuid': book_uuid,
            'flow_uuid': flow_uuid,
        }

    def process(self, msg, kwargs):
        prefix = '[%(job_name)s(%(book_uuid)s+%(flow_uuid)s)]' % self.extra
        msg, kwargs = self.logger.process(msg, kwargs)
        msg = '%s %s' % (prefix, msg)
        return msg, kwargs
