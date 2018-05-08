# -*- coding: utf-8 -*-
from nebula.core.i18n import _
from nebula.core import constants


def job_fa(state):
    if state in constants.JOB_STATUS_SUCCESS_LIST:
        return 'fa fa-check'
    elif state in constants.JOB_STATUS_FAILURE_LIST:
        return 'fa fa-times'
    elif state in constants.JOB_STATUS_RUNNING_LIST or \
            state in constants.JOB_STATUS_PENDING_LIST:
        return 'timer'
    return ''


def job_text(state):
    if state in constants.JOB_STATUS_SUCCESS_LIST:
        return 'text-success'
    elif state in constants.JOB_STATUS_FAILURE_LIST:
        return 'text-error'
    elif state in constants.JOB_STATUS_RUNNING_LIST or \
            state in constants.JOB_STATUS_PENDING_LIST:
        return ''
    return ''


def job_state_humanize(state):
    if state in constants.JOB_STATUS_SUCCESS_LIST:
        return ''
    elif state in constants.JOB_STATUS_FAILURE_LIST:
        return ''#_(u"失败")
    elif state in constants.JOB_STATUS_RUNNING_LIST:
        return _(u"任务中")
    elif state in constants.JOB_STATUS_PENDING_LIST:
        return _(u"等待中")
    return ''


def job_state_class(state):
    if state in constants.JOB_STATUS_SUCCESS_LIST:
        return ''
    elif state in constants.JOB_STATUS_FAILURE_LIST:
        return 'text-error'
    elif state in constants.JOB_STATUS_RUNNING_LIST or state in constants.JOB_STATUS_PENDING_LIST:
        return 'text-success'
    return ''
