# -*- coding: utf-8 -*-

#import pytest
from invoke import task

from oslo.config import cfg

from nebula.core import quota
from nebula.core.context import RequestContext
from nebula.core.managers import managers

CONF = cfg.CONF.import_group('quota', 'nebula.core.quota')

QUOTAS = quota.QUOTAS

user_id = 1

context = RequestContext(user_id)


@task
def get_user_quotas():
    result = QUOTAS.get_user_quotas(context, user_id)

    print 'result....'
    print '***********'
    print result


@task
def get_by_user():
    result = QUOTAS.get_by_user(context, user_id, ['instances'])

    print 'result....'
    print '***********'
    print result


@task
def reserve():
    print QUOTAS.reserve(context, **{'instances': 1, 'cores': 2})


@task
def commit():
    reservations = ['e176356e-1859-11e4-a11d-20c9d080cf59']
    print QUOTAS.commit(context, reservations, user_id)


@task
def rollback():
    reservations = ['f0942f42-15f7-11e4-aef7-20c9d080cf59']
    print QUOTAS.rollback(context, reservations, user_id)


@task
def test_compute():
    print 'Testing'
    ret = managers.compute_nodes.get_host_exclude_instance(2)
    print ret