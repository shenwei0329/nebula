#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#   Mongodb工作日志导入MySql
#   ========================
#   2018年3月16日@成都
#
#

import MySQLdb
import sys
import json
import time
import os
import datetime
import types
import doPie
import doHour
import doBox
from docx.enum.text import WD_ALIGN_PARAGRAPH
import crWord
import showJinkinsRec
import showJinkinsCoverage
import mongodb_class
import jira_class_epic
import re
import pandas as pd
import mysql_hdr

reload(sys)
sys.setdefaultencoding('utf-8')

from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']


def load_worklog(mysql_db, mongo_db, group_name, source):
    """
    将mongodb中的团队worklog记录导入mysql中
    :param mysql_db: mysql数据源
    :param mongo_db: mongodb数据源
    :param source：项目标识
    :return:
    """
    """ 按 修改日期 升序查询，以确保记录是最新的 """
    _cur = mongo_db.handler('worklog', 'find', {"issue": {'$regex': ".*%s.*" % source}}).sort([('updated', 1)])
    for _event in _cur:
        """
        _sql = 'select count(*) from task_t where TK_RW="%s:%s"' % (source,"%s" % _event['_id'])
        避免工作内容重复的日志
        """
        _str = u"%s" % _event['comment'].replace('\n', '|').replace('\r', '|').replace('"', '^').replace("'", '^')
        if len(_str) > 84:
            _str = _str[4:84]
        _sql = 'select id, TK_GZSJ from task_t where TK_XMBH="%s" and' \
               ' TK_ZXR="%s" AND' \
               ' TK_RWNR like "%%%s%%" AND' \
               ' TK_KSSJ="%s"' \
               % (_event['issue'],
                  u"%s" % _event['author'].strip(' '),
                  _str,
                  ("%s" % _event['started']).replace('T', ' '))
        # print _sql
        _cur = mysql_db.do(_sql)
        if (type(_cur) is types.NoneType) or (len(_cur) == 0) or (type(_cur[0]) is types.NoneType):
            """添加记录"""
            _sql = u'insert into task_t(TK_RW,TK_XMBH,TK_RWNR,TK_KSSJ,TK_GZSJ,TK_ZXR,TK_SQR,created_at) ' \
                   u'values("%s","%s","%s","%s","%s","%s","%s","%s")' %\
                   (("%s:%s" % (source, _event['_id'])),
                    _event['issue'],
                    _event['comment'].replace('\n', '|').replace('\r', '|').replace('"', '^').replace("'", '^'),
                    ("%s" % _event['started']).replace('T', ' '),
                    "%0.2f" % (float(_event['timeSpentSeconds'])/3600.),
                    (u"%s" % _event['author']).strip(' '),
                    group_name,
                    ("%s" % _event['updated']).replace('T', ' '))
            print "--> insert: ", ("%s:%s" % (source, _event['_id']))
            mysql_db.insert(_sql)
        else:
            if _cur[0][1] != "%0.2f" % (float(_event['timeSpentSeconds'])/3600.):
                print "--> update: ", str(_cur[0][0]), ' fr ', _cur[0][1], ' to ', "%0.2f" % (
                            float(_event['timeSpentSeconds']) / 3600.)
                _sql = u'update task_t set TK_GZSJ="%s",TK_RWNR="%s" where id="%s"' % \
                       ("%0.2f" % (float(_event['timeSpentSeconds'])/3600.),
                        _event['comment'].replace('\n', '|').replace('\r', '|').replace('"', '^').replace("'", '^'),
                        str(_cur[0][0]))
                mysql_db.insert(_sql)


def main():

    """MySQL数据库
    """
    mysql_db = mysql_hdr.SqlService(
        MySQLdb.connect(host="47.93.192.232", user="root", passwd="sw64419" ,db="nebula", charset='utf8'))

    group_name = {"FAST": u'云平台研发组',
                  "HUBBLE": u'大数据研发组',
                  "CPSJ": u'产品设计组',
                  "ROOOT": u'系统组',
                  "TESTCENTER": u'测试组'}
    for source in ['FAST', 'HUBBLE', 'CPSJ', 'ROOOT', 'TESTCENTER']:
        """mongoDB数据库
        """
        mongo_db = mongodb_class.mongoDB(source)
        load_worklog(mysql_db, mongo_db, group_name[source], source)


if __name__ == '__main__':

    main()
