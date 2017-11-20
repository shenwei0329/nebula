# coding=utf-8

from flask import g
from wtforms import validators

from nebula.core import models
from nebula.core import constants
from nebula.core.i18n import _


class NebulaValidator(object):

    @property
    def context(self):
        return g.context


def instance_state_check(form, field):
    pass

