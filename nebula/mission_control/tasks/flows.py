# -*- coding: utf-8 -*-

from celery.utils.log import get_task_logger

from nebula.core.mission import helpers as mission_helpers
from nebula.mission_control.app import app
from nebula.core.i18n import _

LOG = get_task_logger(__name__)


@app.task(ignore_result=True)
def execute_job(job_name, book_uuid, flow_uuid, store=None):
    job_context = _("[%(job_name)s(%(book_uuid)s+%(flow_uuid)s)]") % {
        'job_name': job_name,
        'book_uuid': book_uuid,
        'flow_uuid': flow_uuid,
    }

    try:
        LOG.debug(_("%s Loading job from database."), job_context)
        with mission_helpers.load_engine_from_job(
                job_name, book_uuid, flow_uuid, store=store) as engine:
            engine.run()
    except Exception as err:
        LOG.exception(_("%s Job execution failed: %s"), job_context, err)
    else:
        LOG.info(_("%s Job execution succeed."), job_context)
