# -*- coding: utf-8 -*-
from flask import request
from flask import url_for


def redirect_url():
    url = request.args.get('next') or url_for('portal.home')
    return url
