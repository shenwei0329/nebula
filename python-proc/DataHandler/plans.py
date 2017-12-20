#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# 任务计划跟踪器
# ==============
# 2017年12月6日@成都
#
#

import MySQLdb,sys,json, time
import datetime,types
import doPie, doHour, doBox
from docx.enum.text import WD_ALIGN_PARAGRAPH
import crWord

reload(sys)
sys.setdefaultencoding('utf-8')

from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']

"""人天成本"""
CostDay = 1000.
CostHour = CostDay/8.

ProjectAlias = {
    "PRD-2017-PROJ-00003": "FAST",
}

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

def _print(_str, title=False, title_lvl=0, color=None, align=None, paragrap=None ):

    global doc, Topic_lvl_number, Topic

    _str = u"%s" % _str.replace('\r', '').replace('\n','')

    _paragrap = None

    if title:
        if title_lvl==2:
            _str = Topic[Topic_lvl_number] + _str
            Topic_lvl_number += 1
        if align is not None:
            _paragrap = doc.addHead(_str, title_lvl, align=align)
        else:
            _paragrap = doc.addHead(_str, title_lvl)
    else:
        if align is not None:
            if paragrap is None:
                _paragrap = doc.addText(_str, color=color, align=align)
            else:
                doc.appendText(paragrap, _str, color=color, align=align)
        else:
            if paragrap is None:
                _paragrap = doc.addText(_str, color=color)
            else:
                doc.appendText(paragrap, _str, color=color)
    print(_str)

    return _paragrap

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
        if type(_n) is types.NoneType:
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

def getQ(cur):
    """
    获取 数据质量 指标
    :param cur: 数据源
    :return: 指标
    """
    _sql = 'select count(*) from jira_task_t'
    _m = doSQLcount(cur, _sql)

    """计划的任务"""
    _sql = 'select task_name,task_level from project_task_t where task_resources<>"#"'
    _res = doSQL(cur, _sql)

    _n = 0
    _kv = {}
    for _name in _res:
        _level = _name[1][:-2]
        _sql = 'select task_name from project_task_t where task_level="%s"' % _level
        _topics = doSQL(cur, _sql)
        for _topic in _topics:
            """构建任务名称"""
            _like_str = "%s-%s" % (_topic[0], _name[0])
            #print _like_str
            """在Jira中查找满足任务名称的项目"""
            _sql = u'select issue_id,summary,users,issue_status from jira_task_t where ' \
                   u'summary like "%%%s%%"' % _like_str
            _tasks = doSQL(cur, _sql)
            for _task in _tasks:
                if not _kv.has_key(_task[0]):
                    _kv[_task[0]] = []
                (_kv[_task[0]]).append([_like_str,_task[1],_task[2],_task[3]])
                _n += 1

    return _kv, _m, _n

def main(project="PRD-2017-PROJ-00003"):

    global doc,ProjectAlias

    """创建word文档实例
    """
    doc = crWord.createWord()
    """写入"主题"
    """
    doc.addHead(u'产品项目计划跟踪报告', 0, align=WD_ALIGN_PARAGRAPH.CENTER)
    #doc.addHead(u'产品项目【%s】' % project, 1, align=WD_ALIGN_PARAGRAPH.CENTER)

    db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    cur = db.cursor()

    _print('>>> 报告生成日期【%s】 <<<' % time.ctime(), align=WD_ALIGN_PARAGRAPH.CENTER)

    """计划期限"""
    _plan_date = []

    """计划拟完成任务量"""
    _plan_quta = []

    """计划投入工时"""
    _plan_work_hour = []

    """实际完成任务量"""
    _active_quta = []
    """修正后的实际完成任务量"""
    _active_ing_quta = []

    """实际投入工时"""
    _active_value = []

    """报告结论"""
    _results = []

    """获取项目计划的起始时间"""
    _sql = 'select start_date from project_task_t where task_level="1"'
    _res = doSQL(cur, _sql)
    _pj_start_date = _res[0][0].replace('年','-').replace('月','-').replace('日','-').split('-')

    _year = int(_pj_start_date[0])
    _month = int(_pj_start_date[1])
    _day = int(_pj_start_date[2])

    _pj_start_date = datetime.date(_year, _month, _day)

    #_sql = 'select end_date from project_task_t where task_resources<>"#" and PJ_XMBH="%s" order by end_date' % project
    _sql = 'select PJ_KSSJ,PJ_JSSJ from project_t where PJ_XMBH="%s"' % project
    _res = doSQL(cur, _sql)

    _str_date = _res[0]
    _start_date = _res[0][0].replace('年','-').replace('月','-').replace('日','').split('-')
    _end_date = _res[0][1].replace('年','-').replace('月','-').replace('日','').split('-')

    _year = int(_start_date[0])
    _month = int(_start_date[1])
    _day = int(_start_date[2])

    start_date = datetime.date(_year, _month, _day)

    _year = int(_end_date[0])
    _month = int(_end_date[1])
    _day = int(_end_date[2])

    end_date = datetime.date(_year, _month, _day)

    _sql = 'select PJ_XMMC,PJ_XMFZR,PJ_KSSJ,PJ_JSSJ,PJ_XMJJ,PJ_XMYS from project_t where PJ_XMBH="%s"' % project
    _res = doSQL(cur, _sql)
    if _res is None or len(_res)==0:
        print("\n\tErr: Invalid number of project: %s)" % project)

    _print(u"项目基本信息", title=True, title_lvl=1)

    _print(u'项目名称：%s' % _res[0][0])
    _print(u'项目编号：%s' % project)
    _print(u'项目负责人：%s' % _res[0][1])
    _print(u'项目起止日期：%s 至 %s' % (_res[0][2], _res[0][3]))
    _print(u'项目预算（工时成本）：%s 万元' % _res[0][5])
    _print(u'项目功能简介：%s' % _res[0][4])

    _pre_cost = float(_res[0][5])

    _kv, _max_n, _act_n = getQ(cur)
    _q = float(_act_n*100)/float(_max_n)
    if _q < 75:
        _print(u'任务分配数据质量：评定为【差】。在已分配的%d个任务中，仅有%d个（占比%0.2f%%）与计划匹配。' %
               (_max_n,_act_n,_q), color=(255,0,0))
    elif _q < 85:
            _print(u'任务分配数据质量：评定为【一般】。在已分配的%d个任务中，有%d个（占比%0.2f%%）与计划匹配。' %
                   (_max_n, _act_n, _q), color=(150, 0, 0))
    else:
        _print(u'任务分配数据质量：评定为【好】。已分配任务%d个，其中有%d个（占比%0.2f%%）与计划匹配。' %
               (_max_n, _act_n, _q))

    """需要在此插入语句"""
    _paragrap = _print(u"计划指标与实际情况", title=True, title_lvl=1)

    """计划
    """
    _print(u"任务数量分布情况", title=True, title_lvl=2)
    """当日完成任务的Σ工时
    """
    _now = datetime.datetime.now()
    _today = datetime.date(_now.year,_now.month,_now.day)

    _start_date = start_date
    _sum = 0
    while True:
        _date = _start_date.strftime(u"%Y年%m月%d日").replace(u'年0', u'年').replace(u'月0', u'月')
        _sql = 'select sum(work_hour) from project_task_t ' \
               'where end_date like "%%%s%%" and task_resources<>"#" and PJ_XMBH="%s" order by task_id' % (_date,project)
        _n = int(doSQLcount(cur,_sql))
        _plan_work_hour.append([_sum, _sum+_n])
        _sum += _n

        _start_date = _start_date + datetime.timedelta(days=1)
        if _start_date > end_date:
            break

    _start_date = start_date
    _sum = 0
    _sum_ing = 0
    _pro_cost = 0
    while True:
        _date = _start_date.strftime("%Y-%m-%d")
        _sql = 'select sum(TK_GZSJ) from task_t ' \
               'where created_at BETWEEN "%s 00:00:00" AND "%s 23:59:59" and TK_XMBH="%s"' % (_date, _date, project)
        _n = int(doSQLcount(cur,_sql))
        _active_value.append([_sum, _sum+_n])
        _sum += _n

        if _start_date >= _pj_start_date:
            _active_ing_quta.append([_sum_ing, _sum_ing + _n])
            _sum_ing += _n
        else:
            _active_ing_quta.append([0, 0])

        _start_date = _start_date + datetime.timedelta(days=1)
        if _start_date == _pj_start_date:
            _pro_cost = _sum
        if _start_date>_today:
            break

    _start_date = start_date
    while True:
        _date = _start_date.strftime(u"%Y年%m月%d日").replace(u'年0', u'年').replace(u'月0', u'月')
        _sql = 'select count(*) from project_task_t ' \
               'where end_date like "%%%s%%" and task_resources<>"#" and PJ_XMBH="%s" order by task_id' % (_date,project)
        _n = int(doSQLcount(cur,_sql))
        _plan_date.append(_start_date)
        _plan_quta.append(_n)

        _start_date = _start_date + datetime.timedelta(days=1)
        if _start_date > end_date:
            break

    _line_n = 0
    _start_date = start_date
    while True:
        _date = _start_date.strftime(u"%Y-%m-%d")
        _sql = 'select count(*) from jira_task_t ' \
               'where project_alias="%s" and endDate like "%%%s%%" and issue_status="完成" order by id' %\
               (ProjectAlias[project],_date)
        _n = int(doSQLcount(cur,_sql))
        _active_quta.append(_n)

        _line_n += 1
        _start_date = _start_date + datetime.timedelta(days=1)
        if _start_date>_today:
            break

    """生成【计划】曲线（数据）"""
    _data = []
    _total = []
    _sum = 0
    for _v in _plan_quta:
        _sum += _v
        _total.append(_sum)
    _data.append([_total, "#8f8f8f", "^", u"计划"])

    """生成【执行】曲线（数据）"""
    _total_complete = []
    _sum = 0
    for _v in _active_quta:
        _sum += _v
        _total_complete.append(_sum)
    _data.append([_total_complete, "#1a1a1a", ".", u"完成"])

    """计算延期（天）"""
    _plan_day = 0
    for _day_quta in _total:
        if _day_quta >= _sum:
            break
        _plan_day += 1
    _delay_day = _line_n - _plan_day

    """形成【计划任务量分布说明】"""
    _lines = [[_line_n, '-', 'red', u'当前日期']]
    __data = [[[range(len(_plan_quta)), _plan_quta], "b", "-", u"当天完成任务数"]]
    _fn = doBox.doStem(u'计划的任务量分布图', u'Δ任务完成数量（个）', u'日期【%s 至 %s】（天）'%
                       (_str_date[0],_str_date[1]), __data, lines=_lines)
    doc.addPic(_fn,sizeof=3.6)
    _print(u'【图例说明】：图示研发计划中任务数量的分配情况。'
           u'横坐标是工作时间，纵坐标是计划当天要完成的任务个数，'
           u'红竖线是当前位置。'
           u'通过图示可大致了解当前是否处于任务的“密集区”。')

    _print(u"资源投入计划与实际情况", title=True, title_lvl=2)

    _ylines = []
    _ylines.append([_plan_work_hour[_line_n][1], '--', 'k', u'计划投入%d个人时' % _plan_work_hour[_line_n][1]])
    _ylines.append([_active_value[_line_n-1][1], '--', 'r', u'实际投入%d个人时' % _active_value[_line_n-1][1]])

    if _active_value[_line_n-1][1]>_plan_work_hour[_line_n][1]:
        _dlt = float((_active_value[_line_n-1][1] - _plan_work_hour[_line_n][1])*100)/float(_plan_work_hour[_line_n-1][1])
        _print(u'【风险提示】：本期项目的实际资源投入（人时费用）已超过计划预期。'
               u'本期计划投入%d个人时，实际投入%d个人时，超出%0.2f%%）。' %
               (_plan_work_hour[_line_n][1], _active_value[_line_n-1][1], _dlt),
               color=(250, 0, 0))
        _print(u'注：在项目立项和设计阶段已投入【%d】个人时。' % _pro_cost, color=(255, 0, 0))
        _v = float(_active_value[_line_n - 1][1]) * CostHour / 10000.0
        _results.append([u'● 【风险提示】资源投入量超出计划%0.2f%%。本期计划投入%d个人时（工时成本%0.2f 万元），'
                         u'实际投入%d个人时（工时成本%0.2f 万元，占预算%0.2f%%）。' %
                         (_dlt,
                          _plan_work_hour[_line_n][1],
                          float(_plan_work_hour[_line_n][1])*CostHour/10000.0,
                          _active_value[_line_n-1][1],
                          _v,
                          _v*100.0/_pre_cost
                          ),
                         (255, 0, 0)])
        if _v/_pre_cost > 1.0:
            _results.append([u'● 【风险提示】资源投入已超预算（超%0.2f万元）。' % (_v - _pre_cost),
                             (255, 0, 0)])
    else:
        _print(u'当前本项目的实际资源投入（人时费用）满足计划要求。')
        _results.append([u'● 资源投入量满足计划预期要求。', None])

    # [[range(len(_active_ing_quta)), _active_ing_quta], "g", "-", u"阶段投入"],
    __data = [[[range(len(_active_value)), _active_value], "r", "-", u"已投入"],
             [[range(len(_plan_work_hour)), _plan_work_hour], "k", "-", u"计划投入"]]
    _fn = doBox.doLine(u'投入分布图', u'Δ投入工时（人时）', u'日期【%s 至 %s】（天）'%(_str_date[0],_str_date[1]),
                       __data, label_pos='upper left', lines=_lines, ylines=_ylines)
    doc.addPic(_fn,sizeof=3.6)
    _print(u'【图例说明】：图示过程中资源（人时）计划和实际投入情况。'
           u'图中，黑纵线段为计划的工时量，红纵线段为实际投入的工时量。'
           u'黑横线为当天计划投入总量；红横线为实际投入总量。')

    _print(u"计划跟踪", title=True, title_lvl=1)

    #_date = _today.strftime(u"%Y-%m-%d")
    #_sql = 'select count(*) from jira_task_t where endDate>"%s" order by id' % _date
    _sql = 'select count(*) from jira_task_t where issue_status="处理中" order by issue_id'
    _n = int(doSQLcount(cur, _sql))
    _sql = 'select count(*) from jira_task_t where issue_status="待办" order by issue_id'
    _m = int(doSQLcount(cur, _sql))
    _sql = 'select count(*) from jira_task_t where issue_status="处理中" and summary like "%入侵%" order by issue_id'
    _r = int(doSQLcount(cur, _sql))
    _sql = 'select count(*) from jira_task_t where issue_status="完成" and summary like "%入侵%" order by issue_id'
    _r_completed = int(doSQLcount(cur, _sql))
    _sql = 'select count(*) from jira_task_t where issue_status="待办" and summary like "%入侵%" order by issue_id'
    _r_waitting = int(doSQLcount(cur, _sql))

    _print(u"● 截至本迭代周期已完成任务有【%d】个。" % _sum)
    if _n > 0:
        _print(u"● 本迭代周期内正在执行的任务有【%d】个。" % _n)
    if _m > 0:
        _print(u"● 本迭代周期内等待执行的任务有【%d】个。" % _m)
    if _r+_r_completed+_r_waitting > 0:
        _print(u"● 非计划类任务有【%d】个，其中已完成%d个、正在执行%d个和待执行%d个。" %
               (_r+_r_completed+_r_waitting, _r_completed, _r, _r_waitting), color=(150, 0, 0))

    _ylines = []
    _ylines.append([_total[_line_n+1], '--', 'k', u'计划完成%d个' % _total[_line_n+1]])
    _ylines.append([_sum+_n, '--', 'r', u'即将完成%d个' % (_sum+_n)])
    _ylines.append([_sum+_n+_m, '--', 'g', u'等待完成%d个' % _m])
    _dlt = float((_total[_line_n + 1] - (_sum + _n)) * 100) / float(_total[_line_n + 1])
    if _dlt > 5:
        _print(u'【风险提示】：本期实际完成的任务总量已“负偏离”计划量（偏离%0.2f%%），估计延期%d个工作日。' %
               (_dlt, _delay_day),
               color=(250, 0, 0))
        _results.append([u'● 【风险提示】完成任务未达到计划要求，负偏离%0.2f%%，估计延期%d个工作日。' %
                         (_dlt, _delay_day), (255, 0, 0)])
    else:
        _results.append([u'● 任务完成情况满足计划要求。', None])

    if _delay_day < 0:
        _results.append([u'● 进度超前计划【%d】个工作日。' % _delay_day, (0, 200, 0)])

    _dots = [[_line_n + 1, _sum + _n, ">", 'r', u"预期（执行中）"],
             [_line_n + 1, _sum + _n + _m, ">", 'g', u"预期（等待中）"]]

    _fn = doBox.doDotBase(u'任务完成趋势图', u'Σ任务数量（个）', u'日期【%s 至 %s】（天）'%
                          (_str_date[0], _str_date[1]),
                          _data, label_pos='upper left', lines=_lines, ylines=_ylines, dots=_dots)

    doc.addPic(_fn,sizeof=5)
    _print(u'【图例说明】：图示该项目计划的完成状态。'
           u'图中包括计划的、已完成的及本期（本迭代周期）将达到的任务数量水平，'
           u'以直观了解该项目的计划与执行是否存在+/-偏差，以及偏差大小。'
           u'图中，黑线为当天计划的目标；红线为即将达到的目标；绿线为本期预定目标。')

    _print(u'本期项目状态：', paragrap=_paragrap)
    for _r in _results:
        _print(_r[0], paragrap=_paragrap, color=_r[1])

    db.close()
    doc.saveFile('%s-proj.docx' % project)

if __name__ == '__main__':

    main()