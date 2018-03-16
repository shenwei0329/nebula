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


def load_worklog(mysql_db, mongo_db, group_name):
    """
    将mongodb中的团队worklog记录导入mysql中
    :param mysql_db: mysql数据源
    :param mongo_db: mongodb数据源
    :return:
    """
    _cur = mongo_db.handler('worklog', 'find', {})
    for _event in _cur:
        _sql = 'select count(*) from task_t where TK_XMBH="%s"' % ("%s" % _event['_id'])[-20:]
        _count = mysql_db.count(_sql)
        if _count == 0:
            """添加记录"""
            _sql = u'insert into task_t(TK_XMBH,TK_RW,TK_RWNR,TK_KSSJ,TK_GZSJ,TK_ZXR,TK_SQR,created_at) ' \
                   u'values("%s","%s","%s","%s","%s","%s","%s","%s")' %\
                   (("%s" % _event['_id'])[-20:],
                    _event['issue'],
                    _event['comment'].replace('\n', '|').replace('\r', '|'),
                    ("%s" % _event['created']).replace('T', ' '),
                    "%0.2f" % (float(_event['timeSpentSeconds'])/3600.),
                    _event['author'],
                    group_name,
                    ("%s" % _event['updated']).replace('T', ' '))
            print _sql
            mysql_db.insert(_sql)


def main():

    """MySQL数据库
    """
    mysql_db = mysql_hdr.SqlService(
        MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8'))

    group_name = {"FAST": u'云平台研发组',
                  "HUBBLE": u'大数据研发组',
                  "CPSJ": u'产品设计组',
                  "ROOOT": u'系统组',
                  "TESTCENTER": u'测试组'}
    for source in ['FAST', 'HUBBLE', 'CPSJ', 'ROOOT', 'TESTCENTER']:
        """mongoDB数据库
        """
        mongo_db = mongodb_class.mongoDB(source)
        load_worklog(mysql_db, mongo_db, group_name[source])


if __name__ == '__main__':

    main()
