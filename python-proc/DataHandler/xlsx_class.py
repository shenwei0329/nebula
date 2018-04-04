#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# XLSX 文件解析器
# ===============
# 2017年10月10日@成都
#
#
#

import sys

"""设置字符集
"""
reload(sys)
sys.setdefaultencoding('utf-8')

import xlrd
import time
from datetime import datetime


class xlsx_handler:

    def __init__(self, pathname):
        self.data = xlrd.open_workbook(pathname)
        self.table = self.data.sheets()[0]
        self.nrows = self.table.nrows

    def getNrows(self):
        return self.nrows

    def getData(self, row, col):
        """
        获取xlsx记录单元的数据
        :param table: 数据源
        :param row: 行号
        :param col: 列号
        :return:
        """
        try:
            return self.table.row_values(row)[col]
        except:
            return None

    def getXlsxHead(self):
        """
        解析文件头
        :return:
        """
        '''获取表名'''
        _type = self.getData(0, 0)
        _ctype = self.table.cell(0, 0).ctype
        if _ctype != 1:
            _type = None

        '''获取操作类型'''
        _op = self.getData(0, 1).upper()
        _ctype = self.table.cell(0, 1).ctype
        if _ctype != 1:
            _op = 'UPDATE'

        '''获取表项个数'''
        _nrec = self.getData(0, 2)
        _ctype = self.table.cell(0, 2).ctype
        if _ctype == 2 or _ctype == 1:
            _nrec = int(_nrec)
        else:
            _nrec = 0

        '''获取记录类型，目前只支持LIST'''
        _rec = self.getData(0, 3)
        _ctype = self.table.cell(0, 3).ctype
        if _ctype != 1:
            _rec = 'LIST'

        '''获取关键字index'''
        _key = self.getData(0, 4)
        _ctype = self.table.cell(0, 4).ctype
        if _ctype == 1:
            _key = _key.split(',')
        elif _ctype == 0:
            _key = ['0', '']
        elif _ctype == 2:
            # print(">>>_key=[%d]" % _key)
            _key = [str(int(_key)), '']
        else:
            _key = None

        if _key is not None:
            _err = False
            for _v in _key:
                # print(">>>_v=[%s]" % _v)
                if len(_v) > 0:
                    if _nrec is not None and int(_v) >= _nrec:
                        print(">>>Invalid key[%d of %d]" % (int(_v), _nrec))
                        _err = True
                # print(">>>_v=[%s].ed" % _v)
            if _err:
                _key = None
        # print _key
        # print _type,_op,_nrec,_rec,_key
        return _type, _op, _nrec, _rec, _key

    def getXlsxColName(self, nCol):

        _col = []
        for i in range(nCol):
            _colv = self.table.row_values(1)[i]
            _col.append(_colv)
            # print(">>>Col[%s]" % _colv)
        return _col

    def getXlsxRow(self, i, nCol, lastRow):

        # print("%s- getXlsxRow[%d,%d]" % (time.ctime(), i, nCol))

        """ctype : 0 empty,1 string, 2 number, 3 date, 4 boolean, 5 error
        """
        _row = []
        for _i in range(nCol):
            __row = self.table.row_values(i)[_i]
            __ctype = self.table.cell(i, _i).ctype
            # print __row,__ctype
            if __ctype == 3:
                _date = datetime(*xlrd.xldate_as_tuple(__row, 0))
                __row = _date.strftime('%Y/%m/%d')
                __row = __row.split('/')
                __row = u"%d年%d月%d日" % (int(__row[0]), int(__row[1]), int(__row[2]))
            elif __ctype == 2:
                __row = str(__row).replace('.0','')
            elif __ctype == 5:
                __row = ''
            _row.append(__row)

        # print _row

        row = []
        _i = 0
        for _r in _row:

            # print(">>>[%s]" % _r)

            if _r is None or len(str(_r)) == 0:
                if lastRow is not None:
                    _r = lastRow[_i]
            # print _r
            row.append(_r)
            _i = _i + 1
        return row

