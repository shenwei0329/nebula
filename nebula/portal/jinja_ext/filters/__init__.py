# -*- coding: utf-8 -*-

from nebula.portal.jinja_ext.filters.jobs import job_fa
from nebula.portal.jinja_ext.filters.jobs import job_text
from nebula.portal.jinja_ext.filters.jobs import job_state_humanize
from nebula.portal.jinja_ext.filters.jobs import job_state_class
from nebula.portal.jinja_ext.filters.size import human_size
from nebula.portal.jinja_ext.filters.size import percent
from nebula.portal.jinja_ext.filters.time import timesince
from nebula.portal.jinja_ext.filters.time import format_datetime
from nebula.portal.jinja_ext.filters.users import user_online_status
from nebula.portal.jinja_ext.filters.quotas import quota_resource_cn_name
from nebula.portal.jinja_ext.filters.quotas import quota_unit
from nebula.portal.jinja_ext.filters.quotas import quota_default_value
from nebula.portal.jinja_ext.filters.yesno import yes_no
from nebula.portal.jinja_ext.filters.interface import usages
from nebula.portal.jinja_ext.filters.size import bt_to_g
from nebula.portal.jinja_ext.filters.network import first_ip
from nebula.portal.jinja_ext.filters.network import last_ip
from nebula.portal.jinja_ext.filters.i18n import gettext
from nebula.portal.jinja_ext.filters.encoding import decode

def register_filters(app):
    app.jinja_env.filters['user_status'] = user_online_status
    app.jinja_env.filters['timesince'] = timesince
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['human_size'] = human_size
    app.jinja_env.filters['job_fa'] = job_fa
    app.jinja_env.filters['job_text'] = job_text
    app.jinja_env.filters['job_state_humanize'] = job_state_humanize
    app.jinja_env.filters['job_state_class'] = job_state_class
    app.jinja_env.filters['quota_cn_name'] = quota_resource_cn_name
    app.jinja_env.filters['quota_unit'] = quota_unit
    app.jinja_env.filters['quota_default_value'] = quota_default_value
    app.jinja_env.filters['yesno'] = yes_no
    app.jinja_env.filters['percent'] = percent
    app.jinja_env.filters['usages'] = usages
    app.jinja_env.filters['bt_to_g'] = bt_to_g
    app.jinja_env.filters['first_ip'] = first_ip
    app.jinja_env.filters['last_ip'] = last_ip
    app.jinja_env.filters['translate'] = gettext
    app.jinja_env.filters['decode'] = decode
