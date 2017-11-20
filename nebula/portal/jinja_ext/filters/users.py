# -*- coding: utf-8 -*-

from nebula.portal.utils.user import User


def user_online_status(user_id):
    if not user_id:
        return False
    return True if User(user_id).get_status() else False