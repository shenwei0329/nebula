#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#   mongoDB处理机
#   =============
#   2018.2.8
#
#   基于mongoDB处理FAST项目的跟踪、汇总统计和风险评估等
#
#

from pymongo import MongoClient


class mongoDB:

    def __init__(self):
        self.mongo_client = MongoClient()
        self.mongo_db = self.mongo_client.FAST
        self.obj = {"project": self.mongo_db.project,
                    "issue": self.mongo_db.issue,
                    "issue_link": self.mongo_db.issue_link,
                    "log": self.mongo_db.log}
        self.pj_hdr = {"insert": self._insert,
                       "update": self._update,
                       "find": self._find,
                       "find_one": self._find_one,
                       "remove": self._remove}

    @staticmethod
    def _insert(obj, *data):
        return obj.insert(*data)

    @staticmethod
    def _update(obj, *data):
        if obj == "log":
            return None
        return obj.update(*data)

    @staticmethod
    def _find(obj, *data):
        return obj.find(*data)

    @staticmethod
    def _find_one(obj, *data):
        return obj.find_one(*data)

    @staticmethod
    def _remove(obj, *data):
        return None

    def handler(self, obj, operation, *data):
        """
        项目类操作
        :param obj: 目标定义
        :param operation: 操作定义，[insert, update, find, fine_one, remove]
        :param data: 参数
        :return:
        """
        return self.pj_hdr[operation](self.obj[obj], *data)

    def get_count(self, obj, *data):
        """
        获取记录个数
        :param obj: 目标定义
        :param data: 条件
        :return:
        """
        _unit = self.handler(obj, "find", *data)
        return _unit.count()

