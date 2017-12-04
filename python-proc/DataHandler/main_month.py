#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# 月报生成器
# ===============
# 2017年11月27日@成都
#
# 功能：基于库数据，生成月报内容。
#

import MySQLdb,sys,json,time,math
import doPie, doHour, doCompScore, doBox, doBarOnTable
from docx.enum.text import WD_ALIGN_PARAGRAPH
import crWord

reload(sys)
sys.setdefaultencoding('utf-8')

from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']

"""定义时间区间
"""
st_date = '2017-10-30'
ed_date = '2017-12-3'
numb_days = 25
workhours = numb_days * 8

"""指标标题
"""
QT_TITLE = '2017年11月份月报'

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

SpName = [u'杨飞', u'沈伟', u'谭颖卿', u'吴丹阳', u'吴昱珉', u'张志英']

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
        if title_lvl==2:
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
        if _n is None:
            _n = 0
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

def getSum(cur,_days):
    """
    计算时间段内新增记录总条数
    :param cur:
    :param _days:
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
        _sql = 'select count(*) from ' + str(_row[0]) + ' where date(created_at)>DATE_SUB(CURDATE(),INTERVAL %d DAY)' % _days
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
        _print("产品 %s %s 本月处于【%s】状态" % (_row[0], _row[1], _row[2]))

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

def getTstRcdList(cur):
    _sql = 'select err_summary,err_type,err_state,err_pj_name,err_level,err_rpr,err_mod_1 from testrecord_t' + " where created_at between '%s' and '%s'" % (st_date, ed_date)
    _res = doSQL(cur,_sql)
    for _row in _res:
        _pd_v = _row[3].split('^')
        _pd = _pd_v[0]
        _version = _pd_v[1]

        _print(">>>[%s].[%s]" % (_pd,_version))

def getTstLevel(cur,pj_name, flg):
    """
    获取项目测试的 各等级的 统计数
    :param cur:
    :param pd_name:
    :return:
    """

    _l = []
    for _lvl in ['致命', '严重', '一般', '轻微']:
        _sql = 'select count(*) from testrecord_t where err_pj_name="%s" and err_level="%s"' % (pj_name, _lvl)
        if flg==0:
            _sql = _sql + ' and err_state<>"已解决" and err_state<>"已关闭"'
        elif flg==1:
            _sql = _sql + ' and err_state="已解决"'
        else:
            _sql = _sql + ' and err_state="已关闭"'
        _sql = _sql + " and created_at between '%s' and '%s'" % (st_date, ed_date)
        _n = doSQLcount(cur,_sql)
        if _n>0:
            _l.append((_lvl, _n))
    return _l

def getTstRcdSts(cur):
    '''
    计算 每个产品 的测试工作量
    :param cur:
    :return:
    '''
    global ProductList

    _r_err = []
    """测试项目数统计【未解决的】
    """
    for _pd in ProductList:
        _str = "%s^%s" % (_pd[0],_pd[1])
        _sql = 'select count(*) from testrecord_t where err_pj_name="%s"' % _str
        _sql = _sql + " and err_state<>'已解决' and err_state<>'已关闭' and created_at between '%s' and '%s'" % (st_date, ed_date)
        _n = doSQLcount(cur,_sql)
        if _n>0:
            """级别统计
            """
            _level = getTstLevel(cur, pj_name=_str, flg=0)
            _r_err.append((_pd[0], _pd[1], _n, _level))

    _r_oking = []
    """测试项目数统计【已解决的】
    """
    for _pd in ProductList:
        _str = "%s^%s" % (_pd[0],_pd[1])
        _sql = 'select count(*) from testrecord_t where err_pj_name="%s"' % _str
        _sql = _sql + " and err_state='已解决' and created_at between '%s' and '%s'" % (st_date, ed_date)
        _n = doSQLcount(cur,_sql)
        if _n>0:
            """级别统计
            """
            _level = getTstLevel(cur, pj_name=_str, flg=1)
            _r_oking.append((_pd[0], _pd[1], _n, _level))

    _r_ok = []
    """测试项目数统计【已关闭的】
    """
    for _pd in ProductList:
        _str = "%s^%s" % (_pd[0],_pd[1])
        _sql = 'select count(*) from testrecord_t where err_pj_name="%s"' % _str
        _sql = _sql + " and err_state='已关闭' and created_at between '%s' and '%s'" % (st_date, ed_date)
        _n = doSQLcount(cur,_sql)
        if _n>0:
            """级别统计
            """
            _level = getTstLevel(cur, pj_name=_str, flg=2)
            _r_ok.append((_pd[0], _pd[1], _n, _level))

    return _r_ok, _r_oking, _r_err

def getSumToday(cur):
    _sql = 'select sum(rec_count) from count_record_t where date(created_at)=curdate()'
    _n = doSQLcount(cur,_sql)
    if _n is None:
        _n = 0
    return _n

def getOprWorkTime(cur):

    global TotalMember, orgWT, doc

    _sql = 'select MM_XM from member_t'
    _res = doSQL(cur,_sql)

    TotalMember = 0
    orgWT = ()

    for _row in _res:
        _sql = 'select sum(TK_GZSJ) from task_t where TK_ZXR="' + str(_row[0]) + '"' + " and created_at between '%s' and '%s'" % (st_date, ed_date)
        _n = doSQLcount(cur,_sql)
        if _n is None:
            continue
        if _n>0:
            TotalMember = TotalMember + 1

    _print("在岗总人数：%d" % TotalMember)

    _sql = 'select sum(TK_GZSJ) from task_t' + " where created_at between '%s' and '%s'" % (st_date, ed_date)
    _total_workdays = doSQLcount(cur, _sql)
    if _total_workdays is not None:
        _print("总工作量：%d （工时）" % _total_workdays)
        if _total_workdays > 0:
            _a = TotalMember * 80 * 5
            _b = _total_workdays*1000
            _c = int(_b/_a)
            _s = "工作效率：%d %%" % _c
            if _c > 100:
                _s = _s + "，超标 %0.2f 倍" % float(int(_c)/100.)
            if _c < 100:
                _s = _s + "，剩余 %0.2f 倍" % (1.-float(int(_c)/100.))
    else:
        _s = "工作效率：0%"
    _print(_s)

    _print("1、考勤分布：", title=True, title_lvl=2)
    data1 = getChkOnAm(cur)
    data2 = getChkOnPm(cur)
    if len(data1)>0 and len(data2)>0:
        _f1,_f2,_f3 = doHour.doChkOnHour(data1,data2)
        doc.addPic(_f3)
        doc.addText(u"图1 考勤分布总体情况", align=WD_ALIGN_PARAGRAPH.CENTER)
        doc.addPic(_f1)
        doc.addText(u"图2 考勤（上班时间）分布情况", align=WD_ALIGN_PARAGRAPH.CENTER)
        doc.addPic(_f2)
        doc.addText(u"图3 考勤（下班时间）分布情况", align=WD_ALIGN_PARAGRAPH.CENTER)
    else:
        _print("【无“考勤”数据】")

    _print("2、最耗时的工作（前15名）：", title=True, title_lvl=2)
    _sql = 'select TK_RW,TK_ZXR,TK_GZSJ,TK_XMBH from task_t' + " where created_at between '%s' and '%s' order by TK_GZSJ+0 desc" % (st_date, ed_date)
    _res = doSQL(cur,_sql)
    if len(_res)>0:
        for _i in range(15):
            if str(_res[_i][3]) != "#":
                _print( '%d）'% (_i+1) + str(_res[_i][1]) + ' 执行【' +str(_res[_i][3]) + '，' + str(_res[_i][0]) + '】任务时，耗时 ' + str(_res[_i][2]) + ' 工时')
            else:
                _print( '%d）'% (_i+1) + str(_res[_i][1]) + ' 执行【 非项目类：' + str(_res[_i][0]) + '】任务时，耗时 ' + str(_res[_i][2]) + ' 工时')

    _print("3、明细：", title=True, title_lvl=2)
    _sql = 'select MM_XM from member_t'
    _res = doSQL(cur,_sql)
    for _row in _res:
        _sql = 'select sum(TK_GZSJ) from task_t where TK_ZXR="' + str(_row[0]) + '"' + " and created_at between '%s' and '%s'" % (st_date, ed_date)
        _n = doSQLcount(cur,_sql)
        if _n is None:
            continue
        if _n==0:
            continue

        _color = None
        _s = "[员工：" + str(_row[0])+ "，工作 %d 工时" % _n
        if _n>workhours:
            _s = _s + "，加班 %d 工时" % (_n - workhours) + "，占比 %d %%" % ((_n-workhours)*10/4)
            _color = (255,0,0)
        if _n<workhours:
            _s = _s + "，剩余 %d 工时" % (workhours - _n) + "，占比 %d %%" % ((workhours-_n)*10/4)
            _color = (50, 100, 50)
        _s = _s + ']'
        _print(_s, color=_color)
        orgWT = orgWT + (_n,)

    if len(orgWT)>0:
        _fn = doHour.doOprHour(orgWT)
        doc.addPic(_fn)
        doc.addText(u"图4 本周“人-工时”分布情况", align=WD_ALIGN_PARAGRAPH.CENTER)

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

    _m = 0
    for _row in _res:
        _sql = 'select sum(TK_GZSJ) from task_t where TK_XMBH="' + str(_row[0]) + '"' + " and created_at between '%s' and '%s'" % (st_date, ed_date)
        _n = doSQLcount(cur,_sql)
        if _n is None:
            continue
        _m = _m + _n
        if 'PRD-' in str(_row[0]):
            _pd = _pd + _n
        else:
            _pj = _pj + _n

    _sql = 'select sum(TK_GZSJ) from task_t' + " where created_at between '%s' and '%s'" % (st_date, ed_date)
    _total_workdays = doSQLcount(cur,_sql)
    if _total_workdays > _m:
        _sql = "select TK_RWNR,TK_GZSJ from task_t where TK_XMBH='#' and created_at between '%s' and '%s' order by TK_GZSJ+0 desc" % (st_date, ed_date)
        _res = doSQL(cur,_sql)
        for _row in _res:
            _other = _other + int(_row[1])
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
    _sql = 'select KQ_AM from checkon_t' + " where created_at between '%s' and '%s'" % (st_date, ed_date)
    _res = doSQL(cur,_sql)

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
    _sql = 'select KQ_PM from checkon_t' + " where created_at between '%s' and '%s'" % (st_date, ed_date)
    _res = doSQL(cur,_sql)

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

def statTask(db, cur):
    """
    统计非产品研发任务投入
    :param cur:
    :return:
    """
    _sql = 'select PJ_KEY,id from project_key_t'
    _res = doSQL(cur,_sql)

    if len(_res)>0:
        for _row in _res:
            _sql = 'select sum(TK_GZSJ) from task_t where TK_RWNR like "%%%s%%"' % str(_row[0])
            _sum = doSQLcount(cur, _sql)
            _sql = 'update project_key_t set PJ_COST=%d where id=%d' % (int(_sum), int(_row[1]))
            doSQLinsert(db, cur, _sql)

def calChkOnQ(AvgWorkHour, A=1.38):
    """
    计算出勤指标
    :param AvgWorkHour: 日均工作时间（小时）
    :param A: 规定日工时参量，月为1.38 = log10(24)
    :return:
    """
    if AvgWorkHour>=1:
        return math.log10(AvgWorkHour)/A
    else:
        return 0.0

def calTaskQ(sumPJ, sumOther):
    """
    计算执行任务的评分指标
    :param sumPD: 产品研发类任务总数
    :param sumPJ: 工程项目类任务总数
    :param sumOther: 非计划类任务总数
    :return: 评分
    """
    if sumOther>0 and sumPJ>0:
        _v = math.log10(sumPJ + sumOther)
        _b = math.log10(sumPJ)
        return _b/_v
    elif sumPJ>0 and sumOther==0:
        return 0.8
    elif sumOther>0:
        return 0.75
    return 0.0

def calPlanQ(TotalWrokHour, AvgWordHour):
    """
    计算工作计划的质量指标
    :param TotalWrokDay: 总工时
    :param AvgWordDay: 任务的平均工时
    :return: 指标
    """
    if AvgWordHour>=1:
        return (math.log10(TotalWrokHour) - math.log10(AvgWordHour)) / math.log10(TotalWrokHour)
    else:
        return 1.0

def calScore(vals, A=2.4178):
    """
    计算综合评分
    :param vals: 考核参量数组 =（参量1，参量2，...）
    :param A: 综合系数
    :return: 评分
    """
    return int((vals[0]+vals[1]+vals[2])*100/A)

def getChkOnQGroup(cur, g_name):
    """
    获取 研发小组 考勤数据
    :param cur: 数据源
    :param g_name: 组名
    :return:
    """
    _sql = 'select MEMBER_NAME from pd_group_member_t where GROUP_NAME="%s"' % g_name
    _res = doSQL(cur,_sql)
    _v = ()
    for _m in _res:
        _sql = 'select KQ_AM,KQ_PM from checkon_t where KQ_NAME="%s"' % _m[0] + " and created_at between '%s' and '%s'" % (st_date, ed_date)
        __res = doSQL(cur, _sql)
        for __v in __res:
            _pm = calHour(__v[1])
            _am = calHour(__v[0])
            if (_pm is not None) and (_am is not None) and (_pm > _am):
                _v += ((_pm - _am - 1.0), )
    return _v

def getTaskQGroup(cur, g_name):
    """
    获取 研发小组 任务数据
    :param cur: 数据源
    :param g_name: 组名
    :return:
    """
    _sql = 'select sum(TK_GZSJ) from task_t where TK_XMBH<>"#" and TK_SQR="%s"' % g_name + " and created_at between '%s' and '%s'" % (st_date, ed_date)
    _Pj = doSQLcount(cur, _sql)
    _sql = 'select sum(TK_GZSJ) from task_t where TK_XMBH="#" and TK_SQR="%s"' % g_name + " and created_at between '%s' and '%s'" % (st_date, ed_date)
    _nonPj = doSQLcount(cur,_sql)
    return float(_Pj), float(_nonPj)

def getPlanQGroup(cur, g_name):
    """
    获取 研发小组 计划数据
    :param cur: 数据源
    :param g_name: 组名
    :return:
    """
    _sql = 'select TK_GZSJ from task_t where TK_SQR="%s"' % g_name + " and created_at between '%s' and '%s'" % (st_date, ed_date)
    _res = doSQL(cur,_sql)
    _v = ()
    for __v in _res:
        _v += (int(__v[0]),)
    return _v

def getChkOnQMember(cur, m_name):
    """
    获取 个人 考勤数据
    :param cur: 数据源
    :param m_name: 人名
    :return:
    """
    _sql = 'select KQ_AM,KQ_PM from checkon_t where KQ_NAME="%s"' % m_name + " and created_at between '%s' and '%s'" % (st_date, ed_date)
    __res = doSQL(cur, _sql)
    _v = ()
    for __v in __res:
        _pm = calHour(__v[1])
        _am = calHour(__v[0])
        if (_pm is not None) and (_am is not None) and (_pm > _am):
            _v += ((_pm - _am), )
    return _v

def getTaskQMember(cur, m_name):
    """
    获取 个人 任务数据
    :param cur: 数据源
    :param m_name: 人名
    :return:
    """
    _sql = 'select sum(TK_GZSJ) from task_t where TK_XMBH<>"#" and TK_ZXR="%s"' % m_name + " and created_at between '%s' and '%s'" % (st_date, ed_date)
    _Pj = doSQLcount(cur, _sql)
    _sql = 'select sum(TK_GZSJ) from task_t where TK_XMBH="#" and TK_ZXR="%s"' % m_name + " and created_at between '%s' and '%s'" % (st_date, ed_date)
    _nonPj = doSQLcount(cur,_sql)
    return float(_Pj), float(_nonPj)

def getPlanQMember(cur, m_name):
    """
    获取 个人 计划数据
    :param cur: 数据源
    :param m_name: 人名
    :return:
    """
    _sql = 'select TK_GZSJ from task_t where TK_ZXR="%s"' % m_name + " and created_at between '%s' and '%s'" % (st_date, ed_date)
    _res = doSQL(cur,_sql)
    _v = ()
    for __v in _res:
        _v += (int(__v[0]),)
    return _v

def getChkOnQDesc(Q):

    if Q>0.65:
        _desc = u"超标"
    elif Q>0.63:
        _desc = u"正常"
    else:
        _desc = u"不达标"
    return _desc

def getTaskQDesc(Q):
    if Q>0.85:
        _desc = u"偏向项目类事务"
    elif Q>0.73:
        _desc = u"适中"
    else:
        _desc = u"偏向非项目类事务"
    return _desc

def getPlanQDesc(Q):
    if Q>0.85:
        _desc = u"优"
    elif Q>0.75:
        _desc = u"良"
    elif Q > 0.55:
        _desc = u"中"
    elif Q > 0.35:
        _desc = u"弱"
    else:
        _desc = u"差"
    return _desc

def getScoreDesc(chkonQ, taskQ, planQ):
    _desc = u'●出勤：' + getChkOnQDesc(chkonQ)
    _desc += "\n"

    _desc += u'●任务：' + getTaskQDesc(taskQ)
    _desc += "\n"

    _desc += u'●计划：' + getPlanQDesc(planQ)
    return ('text',_desc)

def statGroupInd(cur):
    """创建一个表格 1 x 3"""

    global workhours

    _width = (4,1.8,1.8,2,8)
    doc.addTable(1, 5, col_width=_width)
    _title = (('text',u'研发小组'),('text',u'综合评分'),('text',u'综合指标'),('text',u'图示'),('text',u'解读'))
    doc.addRow(_title)
    _print("注：综合指标图示的绿色区域为最佳范围：出勤为全勤、计划内任务占比80%、计划颗粒度2小时/任务。")

    _sql = 'select GRP_NAME from pd_group_t'
    _res = doSQL(cur, _sql)

    __chkonQ = 0
    __planQ = 0
    __taskQ = 0
    _N = 0
    for _g in _res:

        if _g[0] == u'研发管理组':
            continue

        _name = ('text',_g[0])

        """计算出勤指标"""
        _v = getChkOnQGroup(cur, _g[0])
        if len(_v)>0:
            _chkonQ = calChkOnQ(sum(_v)/len(_v))
        else:
            _chkonQ = 0

        """计算任务指标"""
        _pd,_other = getTaskQGroup(cur, _g[0])
        _taskQ = calTaskQ(_pd,_other)

        """计算计划指标"""
        _v = getPlanQGroup(cur, _g[0])
        if len(_v)>0:
            _planQ = calPlanQ(workhours, sum(_v)/len(_v))
        else:
            _planQ = 0

        __chkonQ += _chkonQ
        __planQ += _planQ
        __taskQ += _taskQ
        _N += 1

        _score = ('text',str(calScore((_chkonQ,_taskQ,_planQ,))))
        _pref =('text',u'出勤:%0.2f\n任务:%0.2f\n计划:%0.2f' % (_chkonQ, _taskQ, _planQ))
        _pic = ('pic',doCompScore.doCompScore([u'任务指标',u'出勤指标',u'计划指标'],(_taskQ, _chkonQ, _planQ,),(0.8,0.6544,0.8634,)),1.4)
        _desc = getScoreDesc(_chkonQ, _taskQ, _planQ)
        _col =(_name,_score,_pref,_pic,_desc)
        doc.addRow(_col)

    __chkonQ = __chkonQ/_N
    __taskQ = __taskQ/_N
    __planQ = __planQ/_N
    _score = ('text', str(calScore((__chkonQ, __taskQ, __planQ,))))
    _pref = ('text', u'出勤:%0.2f\n任务:%0.2f\n计划:%0.2f' % (__chkonQ, __taskQ, __planQ))
    _pic = ('pic', doCompScore.doCompScore([u'任务指标',u'出勤指标',u'计划指标'], (__taskQ, __chkonQ, __planQ,), (0.8, 0.6544, 0.8634,)), 1.4)
    _desc = getScoreDesc(__chkonQ, __taskQ, __planQ)
    _col = (('test',u'综合'), _score, _pref, _pic, _desc)
    doc.addRow(_col)
    doc.setTableFont(8)

def statPersonalInd(cur):
    """创建一个表格 1 x 3"""
    _width = (4,1.8,1.8,2,8)
    doc.addTable(1, 5, col_width=_width)
    _title = (('text',u'员工'),('text',u'个人评分'),('text',u'综合指标'),('text',u'图示'),('text',u'解读'))
    doc.addRow(_title)
    _print("注：综合指标图示的绿色区域为最佳范围：出勤为全勤、计划内任务占比80%、计划颗粒度2小时/任务。")

    _sql = 'select MM_XM from member_t'
    _res = doSQL(cur, _sql)
    for _g in _res:

        if _g[0] in SpName:
            continue

        _name = ('text',_g[0])

        """计算出勤指标"""
        _v = getChkOnQMember(cur, _g[0])
        if len(_v)>0:
            _chkonQ = calChkOnQ(sum(_v)/len(_v))
        else:
            _chkonQ = 0

        """计算任务指标"""
        _pd,_other = getTaskQMember(cur, _g[0])
        _taskQ = calTaskQ(_pd,_other)

        """计算计划指标"""
        _v = getPlanQMember(cur, _g[0])
        if len(_v)>0:
            _planQ = calPlanQ(workhours, sum(_v)/len(_v))
        else:
            _planQ = 0
        _score = ('text',str(calScore((_chkonQ,_taskQ,_planQ,))))
        _pref =('text',u'出勤:%0.2f\n任务:%0.2f\n计划:%0.2f' % (_chkonQ, _taskQ, _planQ))
        _pic = ('pic',doCompScore.doCompScore([u'任务指标',u'出勤指标',u'计划指标'],(_taskQ, _chkonQ, _planQ,),(0.8,0.6544,0.8634,)),0.72)
        _desc = getScoreDesc(_chkonQ, _taskQ, _planQ)
        _col =(_name,_score,_pref,_pic, _desc)
        doc.addRow(_col)
    doc.setTableFont(8)

def addPDList(cur, doc):
    """
    填写【研发投入】表
    :param cur: 数据源
    :param doc: 文档
    :return:
    """
    _sql = 'select PJ_XMBH,PJ_XMMC from project_t where PJ_XMXZ="产品研发"'
    _res = doSQL(cur, _sql)
    _sum = 0
    _vv = []
    _label = []
    _i = 1
    for _pd in _res:
        _sql = 'select sum(TK_GZSJ) from task_t where TK_XMBH="%s"' % _pd[0] + " and created_at between '%s' and '%s'" % (st_date, ed_date)
        _v = doSQLcount(cur,_sql)
        _item = (('text',u'%d、'%_i+_pd[0]),('text',_pd[1]),('text',str(_v)))
        _sum += _v
        _vv.append(int(_v))
        _label.append('%d'%_i)
        _i += 1
        doc.addRow(_item)
    _item = (('text', u'合计'), ('text',''), ('text', str(_sum)))
    doc.addRow(_item)
    doc.setTableFont(8)
    _fn = doBox.doBar(u'产品项目资源投入',u'工时',_label,[(_vv,'#afafaf')])
    doc.addPic(_fn, sizeof=3)
    _print(u"产品项目资源投入图", align=WD_ALIGN_PARAGRAPH.CENTER)

def addNoPDList(cur, doc):
    """
    填写【非研发投入】表
    :param cur: 数据源
    :param doc: 文档
    :return:
    """
    _sql = 'select PJ_XMMC,PJ_COST from project_key_t where PJ_COST+0.>0' + " and created_at between '%s' and '%s'" % (st_date, ed_date) + ' order by PJ_COST+0. desc'
    _res = doSQL(cur, _sql)
    _sum = 0
    _vv = []
    _label = []
    _i = 1
    for _pd in _res:
        _item = (('text',u'%d、'%_i+_pd[0]),('text',str(_pd[1])))
        doc.addRow(_item)
        _d = int(_pd[1])
        _vv.append(_d)
        _label.append('%d' % _i)
        _sum += _d
        _i += 1
    _item = (('text', u'合计'), ('text', str(_sum)))
    doc.addRow(_item)
    doc.setTableFont(8)
    _fn = doBox.doBar(u'工程项目和非项目类资源投入',u'工时',_label,[(_vv,'#afafaf')])
    doc.addPic(_fn,sizeof=3)
    _print(u"工程项目和非项目类资源投入图", align=WD_ALIGN_PARAGRAPH.CENTER)

def getPersonalChkOnData(cur, m_name):
    """
    获取 个人 出勤统计数据
    :param cur:
    :param m_name:
    :return:
    """
    _data = []
    _tot_am = ()
    _tot_pm = ()
    for _w in [u'星期一', u'星期二', u'星期三', u'星期四', u'星期五', u'星期六', u'星期日']:
        _sql = 'select KQ_AM, KQ_PM from checkon_t where KQ_NAME="%s" and KQ_DATE like "%%%s%%"' % (m_name,_w) + " and created_at between '%s' and '%s'" % (st_date, ed_date)
        _chkon = doSQL(cur, _sql)
        _am = ()
        _pm = ()
        for _v in _chkon:
            if (_v is None) or (len(_v)==0):
                continue
            __v = calHour(_v[0])
            if __v is not None:
                _am += (__v,)
            __v = calHour(_v[1])
            if __v is not None:
                _pm += (__v,)
        _tot_am += _am
        _tot_pm += _pm
        _data.append((_am,_pm,))
    _data.append((_tot_am,_tot_pm,))
    return _data

def getGroupChkOnData(cur, g_name):
    """
    获取 研发小组 的出勤数据
    :param cur: 数据源
    :param g_name: 组名
    :return:
    """
    _datas = []
    _sql = 'select MEMBER_NAME from pd_group_member_t where GROUP_NAME="%s"' % g_name
    _res = doSQL(cur,_sql)
    _data_am = [(),(),(),(),(),(),(),()]
    _data_pm = [(),(),(),(),(),(),(),()]
    for _member in _res:
        _personal = getPersonalChkOnData(cur, _member[0])
        _i = 0
        _am = ()
        _pm = ()
        for _week in _personal:
            _am += _week[0]
            _pm += _week[1]

            _data_am[_i] += _am
            _data_pm[_i] += _pm
            _i += 1

    _datas.append(_data_am)
    _datas.append(_data_pm)
    return _datas

def getGroupChkOn(cur, doc):
    """
    生成 研发小组的出勤情况
    :param cur:
    :param doc:
    :return:
    """
    doc.addTable(1, 2)
    _title = (('text',u'组名'),('text',u'出勤情况'))
    doc.addRow(_title)

    _sql = 'select GRP_NAME from pd_group_t where GRP_STATE="1"'
    _res = doSQL(cur, _sql)
    for _g in _res:

        if _g[0] == '研发管理组':
            continue
        _name = ('text',_g[0])
        _datas = getGroupChkOnData(cur, _g[0])
        _fig = ('pic',doBox.doBox(['Mo','Tu','We','Th','Fr','Sa','Su','Avg'],_datas,y_limit=(5.,24.),y_line=(9.,17.5,),y_label='Time',x_label='Week'),2)
        doc.addRow((_name,_fig))
    doc.setTableFont(8)

def getTotalChkOn(cur, doc):
    """
    生成总体出勤情况
    :param cur: 数据源
    :param doc: 文档
    :return:
    """
    _sql = 'select GRP_NAME from pd_group_t where GRP_STATE="1"'
    _res = doSQL(cur, _sql)
    _datas = [[(),(),(),(),(),(),(),()],[(),(),(),(),(),(),(),()]]
    for _g in _res:
        __datas = getGroupChkOnData(cur, _g[0])
        for _i in range(8):
            _datas[0][_i] += __datas[0][_i]
            _datas[1][_i] += __datas[1][_i]

    _fn = doBox.doBox(['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su', '日均'], _datas, y_limit=(5., 24.), y_line=(9., 17.5,),
                y_label='时间', x_label='周')
    doc.addPic(_fn,4)
    _print("图例说明：横向分别列出本月周一至周日以及每日平均的出勤特征，纵向表示时间（包含9:00和17:30两个时间点的红线标度）。方框表示集中分布区域，方框内红线为中位线，两端横线分别为上下边缘，边缘外的点为异常点。")

def getOnDutyPersonalCount(cur):

    _n = 0
    _sql = 'select MM_XM from member_t where MM_ZT=1'
    _res = doSQL(cur, _sql)
    for _m in _res:
        _sql = 'select count(*) from checkon_t where KQ_AM<>"#" and KQ_PM<>"#" and KQ_NAME="%s"  and created_at between "%s" and "%s"' % (_m[0],st_date, ed_date)
        _v = doSQLcount(cur, _sql)
        if _v > 0:
            _n += 1
    return _n

def getTaskStat(cur):
    """
    统计 任务情况
    :param cur: 数据源
    :return: 产品类数量（工时）、工程类数量（工时）和非计划类数量（工时）
    """
    """
    _sql = 'select count(*) from task_t where TK_XMBH like "%PRD%"' + " and created_at between '%s' and '%s'" % (st_date, ed_date)
    _pd = doSQLcount(cur, _sql)

    _sql = 'select count(*) from task_t where TK_XMBH<>"#" and (TK_XMBH not like "%PRD%")' + " and created_at between '%s' and '%s'" % (st_date, ed_date)
    _pj = doSQLcount(cur, _sql)

    _sql = 'select count(*) from task_t where created_at between "%s" and "%s"' % (st_date, ed_date)
    _other = doSQLcount(cur, _sql) - _pd - _pj
    """
    _sql = 'select sum(TK_GZSJ) from task_t where TK_XMBH like "%PRD%"' + " and created_at between '%s' and '%s'" % (st_date, ed_date)
    _pd = doSQLcount(cur, _sql)

    _sql = 'select sum(TK_GZSJ) from task_t where TK_XMBH<>"#" and (TK_XMBH not like "%PRD%")' + " and created_at between '%s' and '%s'" % (st_date, ed_date)
    _pj = doSQLcount(cur, _sql)

    _sql = 'select sum(TK_GZSJ) from task_t where created_at between "%s" and "%s"' % (st_date, ed_date)
    _other = doSQLcount(cur, _sql) - _pd - _pj

    return _pd,_pj,_other

def getWorkHourPerDay(cur):
    """
    统计 日均工作时间（小时）
    :param cur: 数据源
    :return: 日均工作时间
    """
    _hour = 0
    _n = 0
    _sql = "select KQ_AM, KQ_PM from checkon_t where created_at between '%s' and '%s'" % (st_date, ed_date)
    _res = doSQL(cur, _sql)
    for _v in _res:
        if _v[0]=="#" or _v[1]=="#":
            continue
        if '次日' in _v[1]:
            __v = _v[1][-5:]
            _hour += ( 24.0 - calHour(_v[0]) + calHour(__v))
        else:
            _hour += (calHour(_v[1]) - calHour(_v[0]))
        _n += 1
    return _hour/_n

def putGroupInfo(cur, doc):
    _print("研发小组特征", title=True, title_lvl=2)
    _print("1、任务特征", title=True, title_lvl=3)
    _print("表：研发小组工作投入情况", align=WD_ALIGN_PARAGRAPH.CENTER)

    doc.addTable(1, 3)
    _title = (('text',u'产品类'),('text',u'工程类'),('text',u'非计划类'))
    doc.addRow(_title)
    _print("")

    _print("2、出勤特征", title=True, title_lvl=3)
    getGroupChkOn(cur, doc)
    _print("")

def getCostTrendDesc(PdCost, PjCost, OtherCost):

    _str_pd = u'产品项目投入表现出'
    _str_pj = u'工程项目投入表现出'
    _str_other = u'非项目类事务的投入表现出'
    _avg_pd = sum(PdCost)/(len(PdCost)+0.0)
    _avg_other = sum(OtherCost)/(len(OtherCost)+0.0)
    if abs((PdCost[-1]+0.0)-_avg_pd)<=0.15:
        _str_pd += u'【平稳】趋势。'
    elif ((PdCost[-1]+0.0)-_avg_pd)>0.15:
        _str_pd += u'【上升】趋势。'
    else:
        _str_pd += u'【下降】趋势。'

    if abs((PjCost[-1]+0.0)-_avg_other)<=0.15:
        _str_pj += u'【平稳】趋势。'
    elif ((PjCost[-1]+0.0)-_avg_other)>0.15:
        _str_pj += u'【上升】趋势。'
    else:
        _str_pj += u'【下降】趋势。'

    if abs((OtherCost[-1]+0.0)-_avg_other)<=0.15:
        _str_other += u'【平稳】趋势。'
    elif ((OtherCost[-1]+0.0)-_avg_other)>0.15:
        _str_other += u'【上升】趋势。'
    else:
        _str_other += u'【下降】趋势。'

    return _str_pd,_str_pj,_str_other

def statCostTrend(cur, doc):

    _sql = "select date(created_at) from task_t where created_at between '%s' and '%s'" % (st_date, ed_date)
    _res = doSQL(cur, _sql)
    _date_at = []
    _date = ""
    for _v in _res:
        if _date != str(_v[0]):
            _date_at.append(str(_v[0]))
            _date = str(_v[0])

    _pd = []
    _pj = []
    _other = []

    _i = 0
    for _date in _date_at:
        _i += 1
        if _i < len(_date_at):
            _sql = "select sum(TK_GZSJ) from task_t where TK_XMBH like '%%PRD%%' and created_at between '%s' and '%s'" % (_date, _date_at[_i])
        else:
            _sql = "select sum(TK_GZSJ) from task_t where TK_XMBH like '%%PRD%%' and created_at between '%s' and now()" % _date
        __pd = doSQLcount(cur, _sql)
        _pd.append(__pd)
        if _i < len(_date_at):
            _sql = "select sum(TK_GZSJ) from task_t where TK_XMBH='#' and created_at between '%s' and '%s'" % (_date, _date_at[_i])
        else:
            _sql = "select sum(TK_GZSJ) from task_t where TK_XMBH='#' and created_at between '%s' and now()" % _date
        __other = doSQLcount(cur, _sql)
        _other.append(__other)
        if _i < len(_date_at):
            _sql = "select sum(TK_GZSJ) from task_t where created_at between '%s' and '%s'" % (_date, _date_at[_i])
        else:
            _sql = "select sum(TK_GZSJ) from task_t where created_at between '%s' and now()" % _date
        _total = doSQLcount(cur, _sql)
        _pj.append(_total- __pd - __other)

    _y_limit = _total*1.4
    _fn = doBox.doBar('研发资源投入趋势','工时',_date_at,[(_pd,'#afafaf'),(_pj,'#8a8a8a'),(_other,'#fafafa')],label=[u'产品项目',u'工程项目',u'非项目类'],y_limit=_y_limit)
    _print(u'本月研发资源处理事务的情况如图示：')
    doc.addPic(_fn,3)

    _pd,_pj,_other = getCostTrendDesc(_pd, _pj, _other)
    _print(u'本月研发资源投入总趋势：')
    _print(u'\t●  ' + _pd)
    _print(u'\t●  ' + _pj)
    _print(u'\t●  ' + _other)

def getNonProductInfo(cur):
    """
    获取 非产品类项目的 特征值
    :param cur: 数据源
    :return:
    """
    _key = []
    _project = []
    _sql = "select PJ_COST,PJ_KEY,PJ_XMMC from project_key_t order by PJ_COST+0. desc"
    _res = doSQL(cur,_sql)
    for _row in _res:
        if int(_row[0])==0:
            break
        _key.append(_row[1])
        _project.append(_row[2])
    return _key,_project

def getGroupTaskSummary(cur):
    """
    生成 每个研发组 执行的 非产品项目任务 的工时数据
    :param cur: 数据源
    :return:
    """

    _key,_project = getNonProductInfo(cur)

    _sql = 'select GRP_NAME from pd_group_t'
    _res = doSQL(cur,_sql)
    _group = []
    _row = []
    for _g in _res:
        if _g[0] == u'研发管理组':
            continue
        _group.append(_g[0])
    for _task_key in _key:
        _col = []
        for _g in _res:
            if _g[0]==u'研发管理组':
                continue
            _sql = 'select sum(TK_GZSJ) from task_t where TK_SQR="%s" and TK_RWNR like "%%%s%%" and created_at between "%s" and "%s"' % (_g[0],_task_key,st_date, ed_date)
            _n = doSQLcount(cur,_sql)
            _col.append(_n)
        _row.append(_col)

    _fn = doBarOnTable.doBarOnTable(_key,_group,_row)
    return _fn,_project,_key, _row

def main():

    global Topic_lvl_number, TotalMember, orgWT, costProject, fd, st_date, ed_date, numb_days, doc, workhours

    if len(sys.argv) != 4:
        print("\n\tUsage: python %s start_date end_date numb_days\n" % sys.argv[0])
        return

    st_date = sys.argv[1]
    ed_date = sys.argv[2]
    numb_days = sys.argv[3]
    workhours = int(numb_days) * 8

    db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    cur = db.cursor()

    """统计非产品类资源投入（成本）
    """
    statTask(db, cur)
    """获取现有产品信息
    """
    getPdList(cur)

    """创建word文档实例
    """
    doc = crWord.createWord()

    """
    *** 封面 ***
    """
    """写入"主题"
    """
    doc.addHead(u'产品研发中心月报', 0, align=WD_ALIGN_PARAGRAPH.CENTER)

    _print(u'>>> 报告生成日期【%s】 <<<' % time.ctime(), align=WD_ALIGN_PARAGRAPH.CENTER)
    _print("")
    _print(u"【说明】产品研发管理的《月报》拟于每月发布一次，其主要目标是：基于研发管理基础数据如实标定研发资源基本特性，并在数据基础上给出研发资源的有效评价。")

    Topic_lvl_number = 0
    _print(u"数据统计", title=True, title_lvl=1)
    _print(u"总体特征", title=True, title_lvl=2)

    _pd,_pj,_other = getTaskStat(cur)
    _hour = getWorkHourPerDay(cur)
    _print(u"本月在岗 %d 人，执行任务 %d 个（产品类 %d 个、工程类 %d 个和非项目类 %d 个），日均工作时间 %0.2f 小时。" % (getOnDutyPersonalCount(cur),(_pd+_pj+_other),_pd,_pj,_other,_hour))

    _print(u"1、任务执行情况", title=True, title_lvl=3)
    getProjectWorkTime(cur)
    if len(costProject)>0:
        _fn = doPie.doProjectPie(costProject)
        _print(u"产品项目投入：%d【人时】，工时成本 %0.2f【万元】" % (costProject[0], costProject[0]*125.0/10000.0))
        _print(u"工程项目投入：%d【人时】，工时成本 %0.2f【万元】" % (costProject[1], costProject[1]*125.0/10000.0))
        _print(u"非项目类事务投入：%d【人时】，工时成本 %0.2f【万元】" % (costProject[2], costProject[2]*125.0/10000.0))
        _print("")
        _print(u"总投入：%d【人时】，工时成本 %0.2f【万元】" % (sum(costProject), sum(costProject)*125.0/10000.0))
        doc.addPic(_fn, sizeof=2.8)
        _print(u'任务执行资源投入占比', align=WD_ALIGN_PARAGRAPH.CENTER)
    _print(u"2、出勤情况", title=True, title_lvl=3)
    getTotalChkOn(cur, doc)

    _print(u"3、在研产品情况", title=True, title_lvl=3)
    getPdingList(cur)
    _print(u"4、产品交付情况", title=True, title_lvl=3)
    getPdDeliverList(cur)

    #doc.addPageBreak()
    Topic_lvl_number = 0
    _print(u"数据分析与评价", title=True, title_lvl=1)

    _print(u"研发投入趋势分析", title=True, title_lvl=2)
    statCostTrend(cur, doc)
    _print("")

    _print(u'研发组参与工程项目和非项目类任务的明细：')
    _fn,_project,_key,_row = getGroupTaskSummary(cur)
    doc.addPic(_fn,sizeof=6)
    _print(u'研发组投入工程项目和非项目类任务图', align=WD_ALIGN_PARAGRAPH.CENTER)
    _print(u'图例说明：')
    _i = 0
    for _k in range(len(_key)):
        _sum = sum(_row[_i])
        if _sum>0:
            _print(u"\t【%s】表示：%s，投入：%d（人时）" % (_key[_k], _project[_k], _sum))
        _i += 1

    _print("资源投入分类明细", title=True, title_lvl=2)
    _print("1、产品项目类资源投入情况", title=True, title_lvl=3)
    doc.addTable(1, 3)
    _title = (('text',u'项目'),('text',u'名称'),('text',u'投入工时（小时）'))
    doc.addRow(_title)
    addPDList(cur, doc)
    _print("")
    _print("2、工程项目和非项目类资源投入情况", title=True, title_lvl=3)
    doc.addTable(1, 2)
    _title = (('text',u'项目名称'),('text',u'投入工时（小时）'))
    doc.addRow(_title)
    addNoPDList(cur, doc)
    _print("")

    _print("团队、个人综合评价", title=True, title_lvl=2)
    _print("1、团队综合评价", title=True, title_lvl=3)
    statGroupInd(cur)
    _print("")
    _print("2、个人综合评价", title=True, title_lvl=3)
    statPersonalInd(cur)
    _print("")

    db.close()
    doc.saveFile('month.docx')
