#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# 任务计划跟踪器
# ==============
# 2017年12月6日@成都
#
#

import MySQLdb,sys,json, time
import datetime
import doPie, doHour, doBox
from docx.enum.text import WD_ALIGN_PARAGRAPH
import crWord

reload(sys)
sys.setdefaultencoding('utf-8')

from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']

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

def main():

    global doc

    if len(sys.argv) != 2:
        print("\n\tUsage: python %s project_name\n" % sys.argv[0])
        return

    """创建word文档实例
    """
    doc = crWord.createWord()
    """写入"主题"
    """
    doc.addHead(u'产品项目计划跟踪报告', 0, align=WD_ALIGN_PARAGRAPH.CENTER)
    #doc.addHead(u'产品项目【%s】' % sys.argv[1], 1, align=WD_ALIGN_PARAGRAPH.CENTER)

    db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    cur = db.cursor()

    _print('>>> 报告生成日期【%s】 <<<' % time.ctime(), align=WD_ALIGN_PARAGRAPH.CENTER)

    _plan_date = []
    _plan_quta = []
    _plan_work_hour = []
    _active_quta = []

    _sql = 'select end_date from project_task_t where task_resources<>"#" and PJ_XMBH="%s" order by end_date' % sys.argv[1]
    _res = doSQL(cur, _sql)

    _str_date = [ _res[0][0][:_res[0][0].index('日')+1],_res[-1][0][:_res[-1][0].index('日')+1]]
    _start_date = _str_date[0].replace('年','-').replace('月','-').replace('日','').split('-')
    _end_date = _str_date[1].replace('年','-').replace('月','-').replace('日','').split('-')

    _year = int(_start_date[0])
    _month = int(_start_date[1])
    _day = int(_start_date[2])

    start_date = datetime.date(_year, _month, _day)

    _year = int(_end_date[0])
    _month = int(_end_date[1])
    _day = int(_end_date[2])

    end_date = datetime.date(_year, _month, _day)

    _sql = 'select PJ_XMMC,PJ_XMFZR,PJ_KSSJ,PJ_JSSJ,PJ_XMJJ from project_t where PJ_XMBH="%s"' % sys.argv[1]
    _res = doSQL(cur, _sql)
    if _res is None or len(_res)==0:
        print("\n\tErr: Invalid number of project: %s)" % sys.argv[1])

    _print(u"项目基本信息", title=True, title_lvl=1)

    _print(u'项目名称：%s' % _res[0][0])
    _print(u'项目编号：%s' % sys.argv[1])
    _print(u'项目负责人：%s' % _res[0][1])
    _print(u'项目起止日期：%s 至 %s' % (_res[0][2], _res[0][3]))
    _print(u'项目功能简介：%s' % _res[0][4])

    _print(u"计划指标", title=True, title_lvl=1)
    """计划
    """
    _print(u"任务数量分布情况", title=True, title_lvl=2)
    """当日完成任务的Σ工时
    """
    _start_date = start_date
    _sum = 0
    while True:
        _date = _start_date.strftime(u"%Y年%m月%d日").replace(u'年0', u'年').replace(u'月0', u'月')
        _sql = 'select count(*) from project_task_t ' \
               'where end_date like "%%%s%%" and task_resources<>"#" and PJ_XMBH="%s" order by task_id' % (_date,sys.argv[1])
        _n = int(doSQLcount(cur,_sql))
        _plan_work_hour.append([_sum, _sum+_n])
        _sum += _n

        _start_date = _start_date + datetime.timedelta(days=1)
        if _start_date > end_date:
            break

    _start_date = start_date
    while True:
        _date = _start_date.strftime(u"%Y年%m月%d日").replace(u'年0', u'年').replace(u'月0', u'月')
        _sql = 'select count(work_hour) from project_task_t ' \
               'where end_date like "%%%s%%" and task_resources<>"#" and PJ_XMBH="%s" order by task_id' % (_date,sys.argv[1])
        _n = int(doSQLcount(cur,_sql))
        _plan_date.append(_start_date)
        _plan_quta.append(_n)

        _start_date = _start_date + datetime.timedelta(days=1)
        if _start_date > end_date:
            break

    _line_n = 0
    _start_date = start_date
    _now = datetime.datetime.now()
    _today = datetime.date(_now.year,_now.month,_now.day)

    while True:
        _date = _start_date.strftime(u"%Y-%m-%d")
        _sql = 'select count(*) from jira_task_t ' \
               'where completeDate like "%%%s%%" and state="CLOSED" order by id' % _date
        _n = int(doSQLcount(cur,_sql))
        _active_quta.append(_n)

        _line_n += 1
        _start_date = _start_date + datetime.timedelta(days=1)
        if _start_date>_today:
            break

    _lines = [[_line_n, '-', 'red', u'当前日期']]
    _data = [[[range(len(_plan_quta)), _plan_quta], "b", "-", u"当天完成任务数"]]
    _fn = doBox.doStem(u'计划的任务量分布图', u'Δ任务完成数量（个）', u'日期【%s 至 %s】（天）'%(_str_date[0],_str_date[1]), _data, lines=_lines)
    doc.addPic(_fn,sizeof=3)
    _print(u'【图例说明】：用以图示研发计划中任务的分配情况。'
           u'横坐标是时间进程（工作日），纵坐标是计划完成的任务个数。'
           u'图中“红竖线”是当前日期，左边表示拟完成的任务量，右边表示计划中的任务量。'
           u'通过图示，可大致了解当前任务量的完成情况。')

    _print(u"投入分布情况", title=True, title_lvl=2)
    _data = [[[range(len(_plan_work_hour)), _plan_work_hour], "k", "-", u"投入量"]]
    _fn = doBox.doLine(u'投入分布图', u'Δ投入工时', u'日期【%s 至 %s】（天）'%(_str_date[0],_str_date[1]),
                       _data, lines = _lines, limit=[-1,10000])
    doc.addPic(_fn,sizeof=3)
    _print(u'【图例说明】：用以图示研发过程中资源（人时）计划投入情况。'
           u'横坐标是时间进程（工作日），纵坐标是计划投入资源量（人时）。'
           u'通过图示，可大致了解该项目已投入的和还需投入的资源情况。')

    _print(u"计划跟踪", title=True, title_lvl=1)

    _data = []
    _total = []
    _sum = 0
    for _v in _plan_quta:
        _sum += _v
        _total.append(_sum)

    _data.append([_total, "#1a1a1a", "^", u"计划"])

    _total_complete = []
    _sum = 0
    for _v in _active_quta:
        _sum += _v
        _total_complete.append(_sum)

    _data.append([_total_complete, "#8f8f8f", "*", u"完成"])

    _date = _today.strftime(u"%Y-%m-%d")
    _sql = 'select count(*) from jira_task_t where endDate>"%s" order by id' % _date
    _n = int(doSQLcount(cur, _sql))

    _print(u"本迭代周期内正在执行的任务有 %d 个。" % _n)

    if _total[_line_n+1]-(_sum+_n)>int(_total[_line_n+1]*0.1):
        _print(u'【风险提示】：本期迭代后，任务完成总量已“负偏离”计划量的10%，请在下一期迭代过程中修正。',
               color=(250, 0, 0))

    _dots = [[_line_n+1,_sum+_n,">",'r',u"预期"]]

    _fn = doBox.doDotBase(u'任务完成趋势图', u'Σ任务数量（个）', u'日期【%s 至 %s】（天）'%(_str_date[0],_str_date[1]),
                          _data, label_pos=4, lines=_lines, dots=_dots)

    doc.addPic(_fn,sizeof=4.2)
    _print(u'【图例说明】：用以图示该项目计划的完成状态。'
           u'图中包括计划要求；实际执行情况及预期（本迭代周期）将达到的水平。'
           u'通过本图可直观了解该项目的计划与执行是否存在+/-偏差，以及偏差大小。')

    db.close()
    doc.saveFile('%s-proj.docx' % sys.argv[1])

if __name__ == '__main__':

    main()