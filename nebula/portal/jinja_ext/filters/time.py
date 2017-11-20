# -*- coding: utf-8 -*-
from datetime import datetime

import arrow
from flask import current_app


def timesince(dt, default=u"刚刚"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """

    now = datetime.utcnow()
    diff = now - dt

    periods = (
        (diff.days / 365, u"年", u"年"),
        (diff.days / 30, u"月", u"月"),
        (diff.days / 7, u"周", u"周"),
        (diff.days, u"天", u"天"),
        (diff.seconds / 3600, u"小时", u"小时"),
        (diff.seconds / 60, u"分钟", u"分钟"),
        (diff.seconds, u"秒", u"秒"),
    )

    for period, singular, plural in periods:

        if period:
            return u"%d%s前" % (period, singular if period == 1 else plural)

    return default


def format_datetime(input_datetime, format='YYYY-MM-DD HH:mm:ss'):
    #TODO(xuwenbao): 时区修改为从配置文件读取时区
    input_datetime = arrow.get(input_datetime).to('+08:00')
    return input_datetime.format(format)
