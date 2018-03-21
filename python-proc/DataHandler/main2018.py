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
# 2017.11.3：增加测试数据统计；增加各个指标的统计时间区域【st_date,ed_date】
# 2017.11.9：实现自动word文档生成
# 2017.11.17：增加产品工程交付内容
#
# 2018.3.16：内容重新改版！
# 以个人为主题：
#   1）出勤情况
#   2）日常工作及用时
#   3）任务执行情况
#   4）个人业绩指标
#

import MySQLdb
import sys
import json
import time
import os
import doPie
import doHour
import doBarOnTable
from docx.enum.text import WD_ALIGN_PARAGRAPH
import crWord
import types

reload(sys)
sys.setdefaultencoding('utf-8')

from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']

sp_name = [u'杨飞', u'吴昱珉', u'王学凯', u'许文宝',
           u'饶定远', u'金日海', u'沈伟', u'谭颖卿',
           u'吴丹阳', u'查明', u'柏银', u'崔昊之']

"""定义时间区间
"""
st_date = '2017-11-4'
ed_date = '2017-11-6'
numb_days = 5
workhours = 40

"""公司定义的 人力资源（预算）直接成本 1000元/人天，22天/月，128元/人时
"""
CostDay = 128
Tables = ['count_record_t',]
TotalMember = 0
GroupName = [u'产品设计组',u'云平台研发组',u'大数据研发组',u'系统组',u'测试组']
costProject = ()
ProductList = []
doc = None
Topic_lvl_number = 0
Topic = [u'一、',
         u'二、',
         u'三、',
         u'四、',
         u'五、',
         u'六、',
         u'七、',
         u'八、',
         u'九、',
         u'十、',
         u'十一、',
         u'十二、',
         ]

def Load_json(fn):

    try:
        f = open(fn, 'r')
        s = f.read()
        _json = json.loads(s)
        f.close()
        return _json
    except:
        return None

def calHour(_str):
    """
    将时间字符串（HH:MM）转换成工时
    :param _str: 时间字符串
    :return: 工时数（2位小数）
    """
    _s = _str.split(':')
    if len(_s)==2 and str(_s[0]).isdigit() and str(_s[1]).isdigit():
        _h = int(_s[0])
        _m = float("%.2f" % (int(_s[1])/60.))
        return _h + _m
    else:
        return None

def _print(_str, title=False, title_lvl=0, color=None, align=None ):

    global doc, Topic_lvl_number, Topic

    _str = u"%s" % _str.replace('\r', '').replace('\n','')

    if title:
        if title_lvl==1:
            _str = Topic[Topic_lvl_number] + _str
            Topic_lvl_number += 1
        if align is not None:
            doc.addHead(_str, title_lvl, align=align)
        else:
            doc.addHead(_str, title_lvl)
    else:
        if align is not None:
            doc.addText(_str, color=color, align=align)
        else:
            doc.addText(_str, color=color)
    print(_str)

def doSQLinsert(db,cur,_sql):

    #print(">>>doSQL[%s]" % _sql)
    try:
        cur.execute(_sql)
        db.commit()
    except:
        db.rollback()

def doSQLcount(cur,_sql):

    #print(">>>doSQLcount[%s]" % _sql)
    try:
        cur.execute(_sql)
        _result = cur.fetchone()
        _n = _result[0]
    except:
        _n = 0

    #print(">>>doSQLcount[%d]" % int(_n))
    return _n

def doSQL(cur,_sql):

    #print(">>>doSQL[%s]" % _sql)
    cur.execute(_sql)
    return cur.fetchall()

def doCount(db,cur):
    """
    数据总量统计
    :param db:
    :param cur:
    :return:
    """

    global Tables

    _sql = 'show tables'
    _res = doSQL(cur,_sql)

    _total_table = 0
    if _res is not None:
        _total_table = len(_res)

    _total_record = 0
    for _row in _res:
        #print(">>>[%s]",_row[0])
        if _row[0] in Tables:
            continue
        _sql = 'select count(*) from ' + str(_row[0])
        _n = doSQLcount(cur,_sql)
        if _n is None:
            _n = 0
        #print(">>> count=%d" % _n)

        '''
        _sql = 'insert into count_record_t(table_name,rec_count,created_at) values("' + str(_row[0]) +'",'+ str(_n) + ',now())'
        doSQLinsert(db,cur,_sql)
        '''
        _total_record = _total_record + _n

    _print("数据库表总数： %d" % _total_table)
    _print("数据记录总条数： %d" % _total_record)

def getSum(cur):
    """
    计算时间段内新增记录总条数
    :param cur:
    :return:
    """

    global Tables, st_date, ed_date

    _sql = 'show tables'
    _res = doSQL(cur,_sql)

    _total_table = 0
    if _res is not None:
        _total_table = len(_res)

    _total_record = 0
    for _row in _res:
        #print(">>>[%s]",_row[0])
        if _row[0] in Tables:
            continue
        _sql = 'select count(*) from ' + str(_row[0]) + " where created_at between '%s' and '%s'" % (st_date, ed_date)
        _n = doSQLcount(cur,_sql)
        if _n is None:
            _n = 0
        _total_record = _total_record + _n
    return _total_record

def getRisk(cur):
    """
    获取 当前存在的 风险 情况
    :param cur:
    :return:
    """
    _sql = 'select RISK_TITLE, RISK_DESC, created_at from risk_t where FLG=1'
    _res = doSQL(cur,_sql)
    _i = 1
    for _row in _res:
        _print('%d、【%s】：%s，创建于%s' % (_i, str(_row[0]), str(_row[1]), str(_row[2])), color=(250, 0, 0))
        _i += 1
    if _i == 1:
        _print(u'无。')

def getEvent(cur):
    """
    获取 当前存在的 事件 情况
    :param cur:
    :return:
    """
    _sql = 'select EVT_TITLE, EVT_DESC, created_at from event_t where FLG=1'
    _res = doSQL(cur,_sql)
    _i = 1
    for _row in _res:
        _print('%d、【%s】：%s，创建于%s' % (_i, str(_row[0]), str(_row[1]), str(_row[2])))
        _i += 1
    if _i == 1:
        _print(u'无。')

def getPdList(cur):

    global ProductList

    _sql = 'select PD_DH,PD_BBH from product_t'
    _res = doSQL(cur,_sql)
    for _row in _res:
        ProductList.append(_row)

def getPdingList(cur):
    """
    获取 在研 产品的状态
    :param cur:
    :return:
    """
    _sql = 'select PD_DH,PD_BBH,PD_LX from product_t where PD_LX<>"产品"'
    _res = doSQL(cur,_sql)
    for _row in _res:
        _print("产品 %s %s 本周处于【%s】状态" % (_row[0], _row[1], _row[2]))

def getPdDeliverList(cur):
    """
    获取 产品的交付情况
    :param cur:
    :return:
    """
    _n = 1
    for _pd in ProductList:
        _sql = 'select b.PJ_XMMC,a.EG_BH,a.DL_STATE from delivery_t a, project_t b '
        _sql = _sql + 'where a.EG_BH=b.PJ_XMBH and a.PD_DH="%s" and a.PD_VERSION="%s" and b.PJ_XMXZ="工程交付" ' % (_pd[0],_pd[1])
        _sql = _sql + 'order by a.EG_BH'
        _res = doSQL(cur,_sql)
        if len(_res)>0:
            _print("%d）产品 %s %s 交付的工程项目有：" % (_n, _pd[0], _pd[1]))
            _n += 1
            for _row in _res:
                _print(u'\t·项目：%s（%s），状态：%s' % (str(_row[0]), str(_row[1]), str(_row[2])))

def getSumToday(cur):
    _sql = 'select sum(rec_count) from count_record_t where date(created_at)=curdate()'
    _n = doSQLcount(cur,_sql)
    if _n is None:
        _n = 0
    return _n


def getOprWorkTime(cur, mongodb):
    """
    生成个人工时执行情况
    :param cur: 数据源
    :param mongodb：issue数据源
    :return: 内容
    """

    global TotalMember, orgWT, doc

    """考勤情况"""
    _print("1、考勤情况：", title=True, title_lvl=2)
    _print(u'数据来源于“钉钉”考勤系统。')
    data1 = getChkOnAm(cur)
    data2 = getChkOnPm(cur)
    if len(data1)>0 and len(data2)>0:
        _f1, _f2, _f3 = doHour.doChkOnHour(data1, data2)
        doc.addPic(_f3)
        doc.addText(u"图1 考勤分布总体情况", align=WD_ALIGN_PARAGRAPH.CENTER)
        doc.addPic(_f1)
        doc.addText(u"图2 考勤（上班时间）分布情况", align=WD_ALIGN_PARAGRAPH.CENTER)
        doc.addPic(_f2)
        doc.addText(u"图3 考勤（下班时间）分布情况", align=WD_ALIGN_PARAGRAPH.CENTER)
    else:
        _print("【无“考勤”数据】")

    _print("2、请假情况：", title=True, title_lvl=2)
    _print(u'数据来源于“钉钉”考勤系统。')
    doc.addTable(1, 2, col_width=(2, 4))
    _title = (('text', u'名称'), ('text', u'关联的审批单'))
    doc.addRow(_title)
    _sql = 'select KQ_NAME,KQ_REF from checkon_t ' \
           'where KQ_REF != "#" and created_at > "2018-03-19 12:00:00" and' \
           ' str_to_date(KQ_DATE,"%%y-%%m-%%d") between "%s" and "%s"' % (st_date, ed_date)
    _res = doSQL(cur, _sql)
    _old_row = ()
    for _row in _res:
        _text = (('text', u"%s" % _row[0]),
                 ('text', (u"%s" % _row[1]).replace('^',' '))
                 )
        if _old_row != _text:
            doc.addRow(_text)
            _old_row = _text
    doc.setTableFont(8)
    _print("")

    _print("3、工作日志工时统计：", title=True, title_lvl=2)
    _print(u'数据来源于任务管理系统。')
    orgWT = ()
    _sql = 'select MM_XM from member_t'
    _res = doSQL(cur,_sql)
    for _row in _res:

        if u"%s" % _row[0] in sp_name:
            continue

        _sql = 'select sum(TK_GZSJ+0.) from task_t where TK_ZXR="' +\
               str(_row[0]) + '"' +\
               ' and created_at > "2018-03-11"' +\
               ' and str_to_date(TK_KSSJ,"%%Y-%%m-%%d") between "%s" and "%s"' % (st_date, ed_date)
        _res = doSQL(cur, _sql)
        if (type(_res) is types.NoneType) or (type(_res[0][0]) is types.NoneType):
            continue
        print _res[0][0]
        _n = float(_res[0][0])
        if _n == 0.:
            continue

        _color = None
        _s = "[员工：" + str(_row[0]) + "，工作 %0.2f 工时" % _n
        if _n > float(workhours):
            _s = _s + "，加班 %0.2f 工时" % (_n - workhours) + "，占比 %0.2f %%" % ((_n-workhours)*100./workhours)
            _color = (255, 0, 0)
        if _n<workhours:
            _s = _s + "，剩余 %0.2f 工时" % (workhours - _n) + "，占比 %0.2f %%" % ((workhours-_n)*100/workhours)
            _color = (50, 100, 50)
        _s = _s + ']'
        _print(_s, color=_color)
        orgWT = orgWT + (_n,)

    if len(orgWT)>0:
        _fn = doHour.doOprHour(orgWT, workhours)
        doc.addPic(_fn)
        doc.addText(u"图4 本周“人-工时”分布情况", align=WD_ALIGN_PARAGRAPH.CENTER)

    _print("4、工作日志明细：", title=True, title_lvl=2)
    _print(u'数据来源于任务管理系统。')
    doc.addTable(1, 4, col_width=(2, 3, 2, 1))
    _title = (('text', u'名称'), ('text', u'任务'), ('text', u'开始时间'), ('text', u'耗时'))
    doc.addRow(_title)

    _sql = 'select MM_XM from member_t where MM_ZT=1'
    _res = doSQL(cur, _sql)
    for _row in _res:

        if u"%s" % _row[0] in sp_name:
            continue

        _text = (('text', u"%s" % str(_row[0])),
                 ('text', ""),
                 ('text', ""),
                 ('text', "")
                 )
        doc.addRow(_text)
        _sql = 'select TK_XMBH,TK_RWNR,TK_KSSJ,TK_GZSJ from task_t where TK_ZXR="' + \
               str(_row[0]) + '"' + \
               ' and created_at > "2018-03-11"' +\
               ' and str_to_date(TK_KSSJ,"%%Y-%%m-%%d") between "%s" and "%s" order by TK_KSSJ' %\
               (st_date, ed_date)
        __res = doSQL(cur, _sql)
        _tot = 0
        for _item in __res:
            _text = (('text', ""),
                     ('text', (u"%s:%s" % (_item[0], _item[1])).replace('|',"")),
                     ('text', _item[2].split(' ')[0]),
                     ('text', _item[3])
                     )
            doc.addRow(_text)
            _tot += float(_item[3])
        _text = (('text', "-"),
                 ('text', u"小计"),
                 ('text', ""),
                 ('text', "%0.2f" % _tot)
                 )
        doc.addRow(_text)
    doc.setTableFont(8)
    _print("")


def getGrpWorkTime(cur):

    global GroupName

    for _grp in GroupName:

        _g_org = []
        _sql = 'select TK_ZXR from task_t where TK_SQR="' + str(_grp) + '"' + " and created_at between '%s' and '%s'" % (st_date, ed_date)
        _res = doSQL(cur,_sql)
        for _row in _res:
            if _row[0] in _g_org:
                continue
            _g_org.append(_row[0])

        _org_n = len(_g_org)
        if _org_n == 0:
            continue
        _sql = 'select sum(TK_GZSJ) from task_t where TK_SQR="' + str(_grp) + '"' + " and created_at between '%s' and '%s'" % (st_date, ed_date)
        _n = doSQLcount(cur,_sql)
        if _n is None:
            continue
        _color = None
        _s = "● [%s：在岗人数 %d 人" % (str(_grp),_org_n) + "，总工作量 %d 工时" % _n
        _v = workhours * _org_n
        if _n>_v:
            _s = _s + "，加班 %d 工时" % (_n - _v) + "，占比 %d %%" % ((_n-_v)*100/_v)
            _color = (255,0,0)
        elif _n<_v:
            _s = _s + "，剩余 %d 工时" % (_v - _n) + "，占比 %d %%" % ((_v-_n)*100/_v)
            _color = (50, 100, 50)
        _s = _s + ']'
        _print(_s, color=_color)


def getProjectWorkTime(cur):
    '''
    获取项目数据统计信息
    :param cur:
    :return:
    '''

    global TotalMember, costProject

    _pd = 0
    _pj = 0
    _other = 0

    _sql = 'select PJ_XMBH,PJ_XMMC from project_t'
    _res = doSQL(cur,_sql)

    _print(u"1、项目投入情况（含产品研发和工程项目）", title=True, title_lvl=2)

    _m = 0
    for _row in _res:
        _sql = 'select sum(TK_GZSJ) from task_t where TK_XMBH="' + str(_row[0]) + '"' + \
               " and created_at between '%s' and '%s'" % (st_date, ed_date)
        _n = doSQLcount(cur,_sql)
        if _n is None:
            continue
        _m = _m + _n
        if 'PRD-' in str(_row[0]):
            _pd = _pd + _n
            _print("● [在研产品：" + str(_row[1]) + '(' + str(_row[0]) + ")，耗时 %d 工时]" % _n)
        else:
            _pj = _pj + _n
            _print("● [项目：" + str(_row[1]) + '('+str(_row[0])+ ")，耗时 %d 工时]" % _n)

    _print(u"2、非项目投入情况", title=True, title_lvl=2)

    _sql = 'select sum(TK_GZSJ) from task_t' + " where created_at between '%s' and '%s'" % (st_date, ed_date)
    _total_workdays = doSQLcount(cur,_sql)
    if _total_workdays > _m:
        _print("[其他（非立项事务）：总耗时 %d 工时]" % (_total_workdays-_m))
        _sql = "select TK_RWNR,TK_GZSJ from task_t where TK_XMBH='#' and created_at " \
               "between '%s' and '%s' order by TK_GZSJ+0 desc" % (st_date, ed_date)
        _res = doSQL(cur,_sql)
        _i = 0
        _print(u"非立项事务明细（前20个）：")
        for _row in _res:
            if (_row[1] == "#"):
                continue
            if (_i < 20) and (u'假' not in _row[0]):
                _i += 1
                _print("● " + str(_row[0]) + " 耗时 " + str(_row[1]) + " 工时")
        _other = _total_workdays-_m
    if (_pd+_pj+_other)>0:
        costProject = (_pd,_pj,_other,)
    else:
        costProject = ()


def getChkOnAm(cur):
    """
    获取员工上午到岗时间序列
    :param cur:
    :return: 到岗记录时间序列
    """
    """
    _sql = 'select KQ_AM from checkon_t' + " where created_at between '%s' and '%s'" % (st_date, ed_date)
    """
    _sql = 'select KQ_AM from checkon_t' \
           ' where str_to_date(KQ_DATE,"%%y-%%m-%%d") between "%s" and "%s"' % (st_date, ed_date)
    _res = doSQL(cur, _sql)

    _seq = ()
    for _row in _res:
        if _row[0]=='#':
            continue
        _h = calHour(_row[0])
        if _h is None:
            _seq = _seq + (9.0,)
        else:
            _seq = _seq + (_h,)
    return _seq


def getChkOnPm(cur):
    """
    获取员工下班时间序列
    :param cur:
    :return: 下班记录时间序列
    """
    """
    _sql = 'select KQ_PM from checkon_t' + " where created_at between '%s' and '%s'" % (st_date, ed_date)
    """
    _sql = 'select KQ_PM from checkon_t ' \
           ' where str_to_date(KQ_DATE,"%%y-%%m-%%d") between "%s" and "%s"' % (st_date, ed_date)
    _res = doSQL(cur, _sql)

    _seq = ()
    for _row in _res:
        if _row[0]=='#':
            continue
        _h = calHour(_row[0])
        if _h is None:
            _seq = _seq + (17.5,)
        else:
            _seq = _seq + (_h,)
    return _seq


def main():
    """
    周报2018版本主体
    :return: 周报
    """

    global TotalMember, orgWT, costProject, fd, st_date, ed_date, numb_days, doc, workhours

    if len(sys.argv) != 4:
        print("\n\tUsage: python %s start_date end_date numb_days\n" % sys.argv[0])
        return

    st_date = sys.argv[1]
    ed_date = sys.argv[2]
    numb_days = sys.argv[3]
    """按一个工作日8小时计算"""
    workhours = int(numb_days) * 8

    """创建word文档实例
    """
    doc = crWord.createWord()
    """写入"主题"
    """
    doc.addHead(u'产品研发中心周报', 0, align=WD_ALIGN_PARAGRAPH.CENTER)

    db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    cur = db.cursor()

    _print('>>> 报告生成日期【%s】 <<<' % time.ctime(), align=WD_ALIGN_PARAGRAPH.CENTER)

    _print("在研产品情况", title=True, title_lvl=1)
    getPdingList(cur)

    _print("人力资源投入", title=True, title_lvl=1)
    getOprWorkTime(cur, None)

    db.close()
    doc.saveFile('week.docx')
    _cmd = 'python doc2pdf.py week.docx weekly-%s.pdf' % time.strftime('%Y%m%d',time.localtime(time.time()))
    os.system(_cmd)

    """删除过程文件"""
    _cmd = 'del /Q pic\\*'
    os.system(_cmd)
