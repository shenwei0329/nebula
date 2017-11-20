# -*- coding: utf-8 -*-
import multiprocessing


def cpu_count():
    try:
        return multiprocessing.cpu_count() or 1
    except NotImplementedError:
        return 1
