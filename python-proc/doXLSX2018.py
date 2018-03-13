#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# XLSX 文件解析器
# ===============
# 2017年10月10日@成都
#
# 功能：通过解析xlsx文件，把记录数据导入数据库(MySQL)中，导入方式包括：更新/创建、追加。
#
# 2017.10.29：提供APPEND、UPDATE和ADD等三种操作方式，分别用于追加、更改和添加新纪录。
# 2018.3.8：采用直接定义表名。
#
#

import os
import MySQLdb
import sys

"""设置字符集
"""
reload(sys)
sys.setdefaultencoding('utf-8')

import xlrd,time,json
from datetime import datetime
from DataHandler import xlsx_class

def doSQL(_sql):

    print(">>>doSQL[%s]" % _sql)
    db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    cursor = db.cursor()
    try:
        cursor.execute(_sql)
        db.commit()
    except:
        db.rollback()

    db.close()

def doSQLcount(_sql):

    print(">>>doSQLcount[%s]" % _sql)
    db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    cursor = db.cursor()
    try:
        cursor.execute(_sql)
        _result = cursor.fetchone()
        _n = _result[0]
    except:
        db.rollback()
        _n = 0

    db.close()
    print(">>>doSQLcount[%d]" % int(_n))
    return _n

def getKEY(_key):

    print(">>>getKEY ing")
    print _key

    _k = []
    for __k in _key:
        print __k,type(__k)
        if len(__k)>0:
            __k = str(__k)
            print __k,type(__k)
            if not __k.isdigit():
                print("%s- Invalid key[%s]" % (time.ctime(),__k))
                return None
            _k.append(int(__k))
    return _k

def buildSQLwhere(_key,_row,_col):

    print(">>>buildSQLwhere ing")
    _sql = ''
    _k = getKEY(_key)

    print _k

    if _k is None:
        return None
    for _index in _k:
        print(">>>sql:[%s]" % _sql)
        _s =  "%s" % _row[_index]
        '''去掉内容中的空格、回车键等字符
        '''
        _s = _s.replace(' ', '')
        _s = _s.replace('\n', ' ')
        _s = _s.replace('\r', ' ')
        _s = _s.replace('\'', '')
        '''勉强的超长限制
        '''
        if len(_s)>2048:
            _s = _s[:2048]
        _sql = _sql + _col[_index] + "='" + _s + "' AND "
    return _sql[:len(_sql)-5]

def buildSQLset(_key,_row,_col):

    print(">>>buildSQLset ing")
    _key = getKEY(_key)
    if _key is None:
        return None

    print _key
    _sql = ''
    _index = 0
    for _c in _col:
        print _index,_sql,_c
        if _index in _key:
            _index = _index + 1
            continue
        _s =  "%s" % _row[_index]
        '''去掉内容中的空格、回车键等字符
        '''
        _s = _s.replace(' ','')
        _s = _s.replace('\n',' ')
        _s = _s.replace('\r',' ')
        '''勉强的超长限制
        '''
        if len(_s)>2048:
            _s = _s[:2048]
        _sql = _sql + _c + "='" + _s + "',"
        _index = _index + 1
    _sql = _sql + "updated_at=now(),"
    return _sql[:len(_sql)-1]


def doRecord(xlsx_handler, _type, _op, _ncol, _key):
    print(">>>doRecord not support")
    return None


def doList(xlsx_handler, _type, _op, _ncol, _key):

    print("%s- doList ing" % time.ctime())
    _rows = []
    for i in range(2,xlsx_handler.getNrows()):
        '''处理合并项的数据
        '''
        if i > 2:
            _row = xlsx_handler.getXlsxRow(i, _ncol, _rows[i-3])
        else:
            _row = xlsx_handler.getXlsxRow(i, _ncol, None)
        _rows.append(_row)

    _col = xlsx_handler.getXlsxColName(_ncol)

    print("...5")
    print _col

    if len(_rows) > 0:

        if 'APPEND' in _op:
            '''追加方式，如日志记录
            '''
            for _row in _rows:
                _sql = 'INSERT INTO ' + _type + '('
                for _c in _col:
                    _sql = _sql + _c + ','
                _sql = _sql + "created_at,updated_at) VALUES("

                print(u"...6[%s]" % _sql)
                for _r in _row:
                    _r = str(_r).replace('\'', '')
                    _s =  "'%s'" % _r
                    '''去掉内容中的空格、回车键等字符
                    '''
                    _s = _s.replace(' ', '')
                    _s = _s.replace('\n', ' ')
                    _s = _s.replace('\r', ' ')
                    '''勉强的超长限制
                    '''
                    if len(_s)>2048:
                        _s = _s[:2048]
                    print(u"...7[%s]" % _s)
                    _sql = _sql + _s + ','

                _sql = _sql + "now(),now())"
                print(">>>SQL:[%s]" % _sql)
                doSQL(_sql)
        elif 'UPDATE' in _op:
            '''更改方式，如状态改变
            '''

            print(">>>UPDATE ing")

            for _row in _rows:

                '''查询已有记录
                '''
                _sql = 'SELECT count(*) FROM ' + _type + ' WHERE '
                __sql_where = buildSQLwhere(_key, _row, _col)
                if __sql_where is None:
                    return
                _sql = _sql + __sql_where
                print(">>>[%s]" % _sql)
                _n = doSQLcount(_sql)
                if _n > 0:
                    '''修改数据项
                    '''
                    _sql = 'UPDATE ' + _type + ' SET '
                    __sql_set = buildSQLset(_key, _row, _col)
                    print __sql_set
                    if __sql_set is None:
                        return
                    _sql = _sql + __sql_set + ' WHERE ' + __sql_where
                    print(">>>[%s]" % _sql)
                    doSQL(_sql)
                else:
                    '''添加数据项
                    '''
                    _sql = 'INSERT INTO ' + _type + '('
                    for _c in _col:
                        _sql = _sql + _c + ','
                    _sql = _sql + "created_at,updated_at) VALUES("

                    print(u"...6[%s]" % _sql)
                    for _r in _row:
                        _r = str(_r).replace('\'', '')
                        _s = u"'%s'" % _r
                        '''去掉内容中的空格、回车键等字符
                        '''
                        _s = _s.replace(' ','')
                        _s = _s.replace('\n',' ')
                        _s = _s.replace('\r',' ')
                        '''勉强的超长限制
                        '''
                        if len(_s)>2048:
                            _s = _s[:2048]
                        print(u"...7[%s]" % _s)
                        _sql = _sql + _s+ ','

                    _sql = _sql + "now(),now())"
                    print(">>>SQL:[%s]" % _sql)
                    doSQL(_sql)
        elif 'ADD' in _op:
            '''新增方式，只添加新纪录【需要判断该记录是否已有？】
            '''

            print(">>>UPDATE ing")

            for _row in _rows:

                '''查询已有记录
                '''
                _sql = 'SELECT count(*) FROM ' + _type + ' WHERE '
                __sql_where = buildSQLwhere(_key,_row,_col)
                if __sql_where is None:
                    return
                _sql = _sql + __sql_where
                print(">>>[%s]" % _sql)
                _n = doSQLcount(_sql)
                if _n>0:
                    return
                else:
                    '''添加数据项
                    '''
                    _sql = 'INSERT INTO '+ TableDic[_type] + '('
                    for _c in _col:
                        _sql = _sql + _c + ','
                    _sql = _sql + "created_at,updated_at) VALUES("

                    print("...6[%s]" % _sql)
                    for _r in _row:
                        _r = str(_r).replace('\'', '')
                        _s =  "'%s'" % _r
                        '''去掉内容中的空格、回车键等字符
                        '''
                        _s = _s.replace(' ','')
                        _s = _s.replace('\n',' ')
                        _s = _s.replace('\r',' ')
                        '''勉强的超长限制
                        '''
                        if len(_s)>2048:
                            _s = _s[:2048]
                        print("...7[%s]" % _s)
                        _sql = _sql + _s+ ','

                    _sql = _sql + "now(),now())"
                    print(">>>SQL:[%s]" % _sql)
                    doSQL(_sql)


def main():

    filename = sys.argv[1]
    print filename
    xlsx_handler = xlsx_class.xlsx_handler(filename)
    try:
        print("...2")
        _table, _op, _ncol, _rectype, _key = xlsx_handler.getXlsxHead()
        if _ncol is None or _ncol == 0:
            return True

        if _table is None:
            print("%s- Type invalid![None]" % time.ctime())
            return True

        if _rectype is None:
            _rectype = 'UPDATE'

        if _rectype is 'UPDATE' and _key is None:
            print("%s- Record type invalid![UPDATE no Key]" % time.ctime())
            return True

        _table = str(_table).lower()
        print("...3")
        if (_rectype is not None) and ('RECORD' in _rectype):
            print("%s- Type not be LIST" % time.ctime())
            doRecord(xlsx_handler, _table, _op, _ncol, _key)
        else:
            print("...4")
            doList(xlsx_handler, _table, _op, _ncol, _key)
            print("%s- Done" % time.ctime())
        return True

    except:
        print("%s- Done[Nothing to do]" % time.ctime())
        return False


if __name__ == '__main__':
    main()

#
# Eof
