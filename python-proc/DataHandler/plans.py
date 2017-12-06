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
    doc.addHead(u'产品项目【%s】' % sys.argv[1], 1, align=WD_ALIGN_PARAGRAPH.CENTER)

    db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    cur = db.cursor()

    _print('>>> 报告生成日期【%s】 <<<' % time.ctime(), align=WD_ALIGN_PARAGRAPH.CENTER)

    """计划
    """
    _plan_date = []
    _plan_quta = []
    _active_quta = []
    _doing_quta = []

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

    _start_date = start_date
    while True:
        _date = _start_date.strftime(u"%Y年%m月%d日").replace(u'年0', u'年').replace(u'月0', u'月')
        _sql = 'select count(*) from project_task_t ' \
               'where end_date like "%%%s%%" and task_id>1 and task_resources<>"#" and PJ_XMBH="%s" order by task_id' % (_date,sys.argv[1])
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
            break;

    _lines = [[_line_n, '-', 'red', u'当前日期']]
    _data = []
    _data.append([_plan_quta,"#8f8f8f", "*", u"计划"])
    _fn = doBox.doBarBase(u'计划的任务量分布图', u'任务数量（个）', u'日期【%s 至 %s】（天）'%(_str_date[0],_str_date[1]), _data, lines=_lines)
    doc.addPic(_fn,sizeof=5)

    _data = []
    _total = []
    _sum = 0
    for _v in _plan_quta:
        _sum += _v
        _total.append(_sum)

    _data.append([_total,"#8f8f8f", "*", u"计划"])

    _total = []
    _sum = 0
    for _v in _active_quta:
        _sum += _v
        _total.append(_sum)

    _data.append([_total,"#aa0000", "^", u"完成"])

    _date = _today.strftime(u"%Y-%m-%d")
    _sql = 'select count(*) from jira_task_t where endDate>"%s" order by id' % _date
    _n = int(doSQLcount(cur, _sql))
    _dots = [[_line_n+1,_sum+_n,">",'r',u"预计"]]

    _fn = doBox.doBarBase(u'任务完成趋势图', u'任务数量（个）', u'日期【%s 至 %s】（天）'%(_str_date[0],_str_date[1]),
                          _data, label_pos=4, lines=_lines, dots=_dots)

    doc.addPic(_fn,sizeof=5)

    _print(u"本迭代周期内正在执行的任务有 %d 个。" % _n)

    db.close()
    doc.saveFile('%s-proj.docx' % sys.argv[1])

if __name__ == '__main__':

    main()