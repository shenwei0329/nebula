# coding=utf-8
from gevent.fileobject import FileObjectThread


def save_file(dst, stream, buffer_size=16384):
    from shutil import copyfileobj

    _dst = open(dst, 'wb')
    f = FileObjectThread(_dst, 'wb')
    try:
        copyfileobj(stream, _dst, buffer_size)
    finally:
        f.close()
