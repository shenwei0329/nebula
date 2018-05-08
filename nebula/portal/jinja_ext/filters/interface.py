# -*- coding: utf-8 -*-


def usages(data):
    if data <= 20:
        return 4
    elif data <= 40:
        return 3
    elif data <= 60:
        return 2
    else:
        return 1
