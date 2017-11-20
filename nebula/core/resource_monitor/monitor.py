# -*- coding: utf-8 -*-
import sys
import logging
import traceback

from concurrent import futures

from . import pollster

DEFAULT_TIMEOUT = 30 * 60

LOG = logging.getLogger(__name__)


class Error(Exception):
    pass


class ResourceFailureError(Error):
    pass


class ResourceTimeoutError(Error):
    pass


class ResourceChangeMonitor(object):

    def __init__(self, checker):
        """

        :param checker: 资源检查器, 若资源操作成功, 返回`True`；
                        需要再次参与轮询, 返回`False`；
                        若失败, 抛出 `ResourceFailureError` 异常。
        """
        self.checker = checker
        self.future = futures.Future()

    def wait(self, timeout=DEFAULT_TIMEOUT):
        """

        :param timeout:
        :return: True on success
        """
        pollster.GRAND_POLLSTER.register_monitor(self)
        try:
            return self.future.result(timeout)
        except futures.TimeoutError:
            raise ResourceTimeoutError()
        finally:
            pollster.GRAND_POLLSTER.unregister_monitor(self)

    # noinspection PyBroadException
    def poll(self):
        try:
            LOG.info('* Running checker: %s.%s', self.checker.__module__, self.checker.func_name)
            if self.checker():
                self.future.set_result(True)
        except Exception as ex:
            #e = sys.exc_info()[0](traceback.format_exc())
            LOG.exception(ex)
            self.future.set_exception(ex)
