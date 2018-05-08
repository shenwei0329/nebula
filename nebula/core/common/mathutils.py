# coding=utf-8

import math

def bt_to_gb(bytes):
    return math.ceil(bytes/1024.0/1024/1024*100)/100
