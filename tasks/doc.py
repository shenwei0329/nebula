# -*- coding: utf-8 -*-
from invoke import task, run


@task(default=True)
def build():
    run('python setup.py build_sphinx')
