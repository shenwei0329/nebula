# -*- coding: utf-8 -*-
import logging

from flask import session

from nebula.portal.utils.user import User

LOG = logging.getLogger(__name__)
d = {'user': 'shenwei'}
FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT)

def get_current_user():
    logging.warn(">>> shenwei: get_current_user <<<")
    return None


def login_user(request, user):
    session['user'] = {'username': u'沈伟', 'id':1, 'is_super': False}
    logging.warn(">>> shenwei: login_user <<<")
    logging.warn(">>> %s:%s <<<" % (dir(user['user']), user['password'].raw_data))
    return User(1)


def logout_user():
    logging.warn(">>> shenwei: logout_user <<<")
    # User(session['user']['id']).clean_status()
    # 从session中去除 'user' 项
    session.pop('user')

