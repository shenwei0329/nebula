# -*- coding: utf-8 -*-


from nebula.core import constants


def yes_no(state):
    if state == constants.YES:
        return u'是'
    elif state == constants.NO:
        return u'否'

    return u'未知'