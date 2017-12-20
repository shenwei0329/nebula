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
#
#

import sysv_ipc as ipc
import os,MySQLdb,sys

"""表字典
"""
TableDic = {
}

"""设置字符集
"""
reload(sys)
sys.setdefaultencoding('utf-8')

import xlrd,time,json
from datetime import datetime

"""获取message_q，它是针对外部的接口，文件路径是通过它传入的
"""
try:
    q = ipc.MessageQueue(19640419001,ipc.IPC_CREAT | ipc.IPC_EXCL)
except:
    q = ipc.MessageQueue(19640419001)

def Load_Conf():
    global TableDic

    try:
        f = open('/home/shenwei/nebula/python-proc/tabledic.conf','r')
        s = f.read()
        TableDic = json.loads(s)
        f.close()
        print(">>> Loading TableDic OK!")
    except:
        print(">>> Loading TableDic Error!")

"""获取xlsx记录单元的数据
   参数：
   table：表
   col：列号
   row：行号
"""
def getData(table,row,col):
    try:
        return table.row_values(row)[col]
    except:
        return None

"""获取xlsx文件头信息
   包括：
   类型、操作、数据元个数、数据集类型【列表、记录】、关键字
"""
def getXlsxHead(table):

    _type = getData(table,0,0)
    _ctype = table.cell(0,0).ctype
    if _ctype != 1:
        _type = None

    _op = getData(table,0,1)
    _ctype = table.cell(0,1).ctype
    if _ctype != 1:
        _op = 'UPDATE'

    _nrec = getData(table,0,2)
    _ctype = table.cell(0,2).ctype
    if _ctype == 2 or _ctype == 1:
        _nrec = int(_nrec)
    else:
        _nrec = 0

    _rec = getData(table,0,3)
    _ctype = table.cell(0,3).ctype
    if _ctype != 1:
        _rec = 'LIST'

    _key = getData(table,0,4)
    _ctype = table.cell(0,4).ctype
    if _ctype == 1:
        _key = _key.split(',')
    elif _ctype == 0:
        _key = ['0', '']
    elif _ctype == 2:
        print(">>>_key=[%d]" % _key)
        _key = [str(int(_key)),'']
    else:
        _key = None

    if _key is not None:
        _err = False
        for _v in _key:
            print(">>>_v=[%s]" % _v)
            if len(_v)>0:
                if _nrec is not None and int(_v) >= _nrec:
                    print(">>>Invalid key[%d of %d]" % (int(_v),_nrec))
                    _err = True
            print(">>>_v=[%s].ed" % _v)
        if _err:
            _key = None
    print _key
    #print _type,_op,_nrec,_rec,_key
    return _type,_op,_nrec,_rec,_key

def getXlsxColName(table,nCol):

    _col = []
    for i in range(nCol):
        _colv = table.row_values(1)[i]
        _col.append(_colv)
        #print(">>>Col[%s]" % _colv)
    return _col

def getXlsxRow(table,i,nCol,lastRow):

    print("%s- getXlsxRow[%d,%d]" % (time.ctime(),i,nCol))

    """ctype : 0 empty,1 string, 2 number, 3 date, 4 boolean, 5 error
    """
    _row = []
    for _i in range(nCol):
        __row = table.row_values(i)[_i]
        __ctype = table.cell(i, _i).ctype
        #print __row,__ctype
        if __ctype == 3:
            _date = datetime(*xlrd.xldate_as_tuple(__row,0))
            __row = _date.strftime('%Y/%m/%d')
            __row = __row.split('/')
            __row = u"%d年%d月%d日" % (int(__row[0]),int(__row[1]),int(__row[2]))
        elif __ctype == 2:
            __row = str(__row)
        elif __ctype == 5:
            __row = ''
        _row.append(__row)

    #print _row

    row = []
    _i = 0
    for _r in _row:

        #print(">>>[%s]" % _r)

        if _r is None or len(str(_r)) == 0:
            if lastRow is not None:
                _r = lastRow[_i]
        #print _r
        row.append(_r)
        _i = _i + 1
    return row

def doSQL(_sql):

    print(">>>doSQL[%s]" % _sql)
    db = MySQLdb.connect(host="localhost",user="root",passwd="mysqlroot",db="nebula",charset='utf8')
    cursor = db.cursor()
    try:
        cursor.execute(_sql)
        db.commit()
    except:
        db.rollback()

    db.close()

def doSQLcount(_sql):

    print(">>>doSQLcount[%s]" % _sql)
    db = MySQLdb.connect(host="localhost",user="root",passwd="mysqlroot",db="nebula",charset='utf8')
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

def doRecord(table,nrows,_type,_op,_ncol,_key):
    print(">>>doRecord not support")
    return None

def doList(table,nrows,_type,_op,_ncol,_key):

    global TableDic

    print("%s- doList ing" % time.ctime())

    _rows = []
    for i in range(2,nrows):

        '''处理合并项的数据
        '''
        if i>2:
            _row = getXlsxRow(table,i,_ncol,_rows[i-3])
        else:
            _row = getXlsxRow(table, i, _ncol, None)

        _rows.append(_row)

    if 'REQUIRMENT' in _type:
        '''历史遗留问题，处理需求功能列表时，须添加记录域名
        '''
        _col = ['PD_BH','PD_BBH','title','role','requirment','effect','const']
        _pd_bh = getData(table, 0, 5)
        _pd_bbh = getData(table,0, 6)
        print(">>>PD[%s,%s]" % (_pd_bh,_pd_bbh))

        __r = []
        '''添加产品代号和版本
        '''
        for _r in _rows:
            _s = []
            _s.append(_pd_bh)
            _s.append(_pd_bbh)
            if len(_r)==5:
                _r.append(' ')
            __r.append(_s + _r[1:])
        _rows = __r
    else:
        _col = getXlsxColName(table,_ncol)

    print("...5")
    print _col

    if len(_rows)>0:

        if 'APPEND' in _op:
            '''追加方式，如日志记录
            '''
            for _row in _rows:
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
                    _s = _s.replace(' ', '')
                    _s = _s.replace('\n', ' ')
                    _s = _s.replace('\r', ' ')
                    '''勉强的超长限制
                    '''
                    if len(_s)>2048:
                        _s = _s[:2048]
                    print("...7[%s]" % _s)
                    _sql = _sql + _s+ ','

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
                _sql = 'SELECT count(*) FROM ' + TableDic[_type] + ' WHERE '
                __sql_where = buildSQLwhere(_key,_row,_col)
                if __sql_where is None:
                    return
                _sql = _sql + __sql_where
                print(">>>[%s]" % _sql)
                _n = doSQLcount(_sql)
                if _n>0:
                    '''修改数据项
                    '''
                    _sql = 'UPDATE ' + TableDic[_type] + ' SET '
                    __sql_set = buildSQLset(_key,_row,_col)
                    print __sql_set
                    if __sql_set is None:
                        return
                    _sql = _sql + __sql_set + ' WHERE ' + __sql_where
                    print(">>>[%s]" % _sql)
                    doSQL(_sql)
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
        elif 'ADD' in _op:
            '''新增方式，只添加新纪录【需要判断该记录是否已有？】
            '''

            print(">>>UPDATE ing")

            for _row in _rows:

                '''查询已有记录
                '''
                _sql = 'SELECT count(*) FROM ' + TableDic[_type] + ' WHERE '
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

    try:
        m = q.receive(block=False)
        if m:
            try:
                print("...1")
                data = xlrd.open_workbook(m[0])
                table = data.sheets()[0]
                nrows = table.nrows

                print("...2")
                _type,_op,_ncol,_rectype,_key = getXlsxHead(table)
                if _ncol is None or _ncol == 0:
                    return True

                if _type is None:
                    print("%s- Type invalid![None]" % time.ctime())
                    return True

                if _rectype is None:
                    _rectype = 'UPDATE'

                if _rectype is 'UPDATE' and _key is None:
                    print("%s- Record type invalid![UPDATE no Key]" % time.ctime())
                    return True

                _type = str(_type).upper()
                if not TableDic.has_key(_type):
                    print("%s- Type invalid![%s]" % (time.ctime(),_type))
                else:
                    print("...3")
                    if (_rectype is not None) and ('RECORD' in _rectype):
                        print("%s- Type not be LIST" % time.ctime())
                        doRecord(table,nrows,_type,_op,_ncol,_key)
                    else:
                        print("...4")
                        doList(table,nrows,_type,_op,_ncol,_key)
                        print("%s- Done" % time.ctime())
            except:
                print("%s- Xlsx file open Error!" % time.ctime())
            os.remove(m[0])
            return True
    except:
        print("%s- Done[Nothing to do]" % time.ctime())
        return False


if __name__ == '__main__':

    Load_Conf()

    while True:
        if not main():
            break

#
# Eof
