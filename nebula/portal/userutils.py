# -*- coding: utf-8 -*-
import logging

from flask import session

from nebula.portal.utils.user import User

LOG = logging.getLogger(__name__)

def get_current_user():
    return None

def login_user(request, user):
    return None

def logout_user():
    User(session['user']['id']).clean_status()
    # 从session中去除 'user' 项
    session.pop('user')

