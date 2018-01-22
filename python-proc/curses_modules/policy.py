# -*- coding: UTF-8 -*-
#
#   策略类 Policy
#   ==========
#

import random
import time


class Policy:

    def __init__(self):
        random.seed(time)
        self.policy = random.random

    def _func(self):
        return self.policy()

    def getPolicy(self):
        _ret = (self._func(), self._func(), self._func(), self._func(),)
        return _ret
