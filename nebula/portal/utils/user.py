# -*- coding: utf-8 -*-

import uuid
from flask import current_app

class User(object):
    """
    portal user
    """

    def __init__(self, user_id):
        self._online_status_key = 'user:online_status:{0}'.format(user_id)
        self._redis = current_app.redis
        self._timeout = 30 * 60

    def set_status(self):
        self._redis.set(name=self._online_status_key,
                        value=str(uuid.uuid1()), px=self._timeout)

    def get_status(self):
        user_status = self._redis.get
        return user_status if user_status else None

    def clean_status(self):
        self._redis.delete(self._online_status_key)