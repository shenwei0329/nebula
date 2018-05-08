# -*- coding: utf-8 -*-
try:
    import pytest
except:
    pass

from invoke import task


@task(default=True)
def all():
    """
    全部测试
    """
    pytest.main('tests')


@task
def models():
    pytest.main('tests/unit/models')


@task
def views():
    pytest.main('tests/unit/views')
