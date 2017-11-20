# -*- coding: utf-8 -*-
from invoke import task
from invoke import run


@task(default=True)
def testweb():
    run('python2.7 run_test_server.py',
        echo=True,
    )


@task()
def web():
    run('python run_server.py',
        echo=True,
    )

@task
def missions():
    run(
        'celery worker --app=nebula.mission_control.app --pool=eventlet --concurrency=500 --loglevel=INFO',
        echo=True,
    )

@task
def flower(address='0.0.0.0', port=5555):
    from .util import nebula_mission_config

    config = nebula_mission_config()
    run(
        'flower --address={address} --port={port} --broker={broker} --broker_api={broker_api}'.format(
            address=address, port=port, broker=config.missions.BROKER_URL,
            broker_api=config.missions.BROKER_API,echo=True,
        )
    )

@task
def notification():
    run('python run_chameleon_notification.py')


@task
def central():
    run('python run_chameleon_central.py')
