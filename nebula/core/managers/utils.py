# -*- coding: utf-8 -*-


class Transfer(object):

    def __init__(self, message='success'):
        self.code = 0
        self.state = True
        self.entity = None
        self.message = message

    def error(self, message):
        self.code = 100
        self.message = message
        self.state = False

    def record(self, entity, message=None):
        if message:
            self.message = message
        self.entity = entity
        self.state = True

    def to_dict(self):
        data = dict(
            code=self.code,
            message=self.message,
        )
        if not self.state:
            data.update(dict(
                errors={'message': self.message}
            ))
        return data