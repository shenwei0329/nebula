#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# XLSX 文件解析器
# ===============
# 2018年4月2日@成都
#
# 功能：通过解析xlsx文件，把记录数据导入数据库(MongoDB)中，导入方式包括：更新/创建。
#

import os
from DataHandler import mongodb_class
import sys

"""设置字符集
"""
reload(sys)
sys.setdefaultencoding('utf-8')

import xlrd,time,json
from datetime import datetime
from DataHandler import xlsx_class


def doList(xlsx_handler, mongodb, _type, _op, _ncol, _key):

    # print("%s- doList ing" % time.ctime())
    _rows = []
    for i in range(2, xlsx_handler.getNrows()):
        _row = xlsx_handler.getXlsxRow(i, _ncol, None)
        _rows.append(_row)

    _col = xlsx_handler.getXlsxColName(_ncol)

    # print("...5")
    # print _col

    if len(_rows) > 0:

        if 'APPEND' in _op:
            '''追加方式，如日志记录
            '''
            for _row in _rows:

                _value = {}
                _i = 0

                _search = {_col[0]: _row[0]}

                # print _search

                # _v = mongodb.handler(_type, 'find_one', _search)
                # print _v

                for _c in _col:
                    _value[_c] = _row[_i]
                    _i += 1

                # print _type, _value
                try:
                    mongodb.handler(_type, 'update', _search, _value)
                except Exception, e:
                    print "error: ", e
                finally:
                    print '.',
        print "o"


def main():

    filename = "D:\\shenwei\\R&D-MIS-DATABASE\\ext-system\\" + sys.argv[1]
    print filename
    xlsx_handler = xlsx_class.xlsx_handler(filename)
    try:

        _table, _op, _ncol, _rectype, _key = xlsx_handler.getXlsxHead()
        if _ncol is None or _ncol == 0:
            return True

        if _table is None:
            print("%s- Type invalid![None]" % time.ctime())
            return True

        _table = str(_table).lower()
        # print("...3")

        """mongoDB数据库
        """
        mongo_db = mongodb_class.mongoDB('ext_system')
        doList(xlsx_handler, mongo_db, _table, _op, _ncol, _key)

        # print("%s- Done" % time.ctime())
        return True

    except:
        print("%s- Done[Nothing to do]" % time.ctime())
        return False


if __name__ == '__main__':
    main()

#
# Eof
