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
import time
from bson.objectid import ObjectId
import datetime


class mongoDB:

    def __init__(self, project):
        self.sort = None
        # self.mongo_client = MongoClient(host=['172.16.101.117:27017'])
        self.mongo_client = MongoClient(host=['localhost:27017'])
        # self.mongo_db = self.mongo_client.FAST
        self.mongo_db = self.mongo_client.get_database(project)
        self.obj = {"project": self.mongo_db.project,
                    "issue": self.mongo_db.issue,
                    "issue_link": self.mongo_db.issue_link,
                    "log": self.mongo_db.log,
                    "worklog": self.mongo_db.worklog,
                    "changelog": self.mongo_db.changelog,
                    "task_req": self.mongo_db.task_req,
                    "current_sprint": self.mongo_db.current_sprint}
        self.pj_hdr = {"insert": self._insert,
                       "update": self._update,
                       "count": self._count,
                       "find": self._find,
                       "find_with_sort": self._find_with_sort,
                       "find_one": self._find_one,
                       "remove": self._remove}

    @staticmethod
    def _insert(obj, *data):
        return obj.insert(*data)

    @staticmethod
    def _update(obj, *data):
        if obj == "log":
            return None
        return obj.update(*data, upsert=True)

    @staticmethod
    def _count(obj, *data):
        return obj.count(*data)

    @staticmethod
    def _find(obj, *data):
        return obj.find(*data)

    @staticmethod
    def _find_with_sort(obj, *data):
        print "--> _find_with_sort: ", data[0][0], data[0][1]
        return obj.find(data[0][0]).sort(data[0][1])

    @staticmethod
    def _find_one(obj, *data):
        return obj.find_one(*data)

    @staticmethod
    def _remove(obj, *data):
        return None

    @staticmethod
    def get_time(ts):
        """
        从_id获取时标信息
        :param ts: _id
        :return: structure time
        """
        _time_t = int(str(ts)[0:8], base=16)
        return time.localtime(_time_t)

    def handler(self, obj, operation, *data):
        """
        项目类操作
        :param obj: 目标定义
        :param operation: 操作定义，[insert, update, find, fine_one, remove, count]
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

    def objectIdWithTimestamp(self, str_date):
        """
        将“日期”字符串转换成ObjectId，用于_id查询
        :param str_date: 日期字符串
        :return: ObjectId
        """
        from_datetime = datetime.datetime.strptime(str_date,'%Y-%m-%d')
        return ObjectId.from_datetime(generation_time=from_datetime)
