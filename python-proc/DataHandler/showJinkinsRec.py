#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.dates import AutoDateLocator, DateFormatter
from pylab import figure, axes
import MySQLdb, sys, time
import pandas as pd

_test_mod = False

reload(sys)
sys.setdefaultencoding('utf-8')

def doSQL(cur,_sql):

    cur.execute(_sql)
    return cur.fetchall()

def doJinkinsRec(cur):
    """
    绘制 Jinkins 作业分布图
    :param cur: 数据源
    :return: 图文件路径
    """
    """准备数据"""
    _jobs = {}
    #_sql = 'select job_name,date_format(job_timestamp,"%Y-%m-%d %H:%I:%S"),job_result,' \
    _sql = 'select job_name,job_timestamp,job_result,' \
           'job_duration,job_estimatedDuration from ' \
           'jinkins_rec_t order by job_timestamp'
    _res = doSQL(cur, _sql)
    for _rec in _res:
        _key = _rec[0].split(' ')
        if not _jobs.has_key(_key[0]):
            _jobs[_key[0]] = []
        _jobs[_key[0]].append([_key[1], _rec[1], _rec[2], _rec[3]])

    _dots = []
    _lables = []
    _y = 1
    for _key in _jobs:
        for _task in _jobs[_key]:
            if _task[2]=="SUCCESS":
                _dots.append([_task[1], _y, '^', 'k'])
            else:
                _dots.append([_task[1], _y, 'o', 'r'])
        _lables.append("%s:%d" % (_key,len(_jobs[_key])))
        _y += 1

    """作图"""
    rcParams.update({
    'font.family':'sans-serif',
    'font.sans-serif':[u'SimHei'],
    'axes.unicode_minus':False,
    'font.size':8,
    })
    autodates = AutoDateLocator()
    yearsFmt = DateFormatter('%Y-%m-%d %H:%M:%S')
    fig = figure(figsize=[8,12])
    ax = axes()
    fig.autofmt_xdate()                         # 设置x轴时间外观  
    ax.xaxis.set_major_locator(autodates)       # 设置时间间隔  
    ax.xaxis.set_major_formatter(yearsFmt)      # 设置时间显示格式  
    ax.set_xticks(pd.date_range(start='2017-12-01 00:00:00', end='2018-01-31 23:59:59', freq='3D'))
    ax.set_xlim("2017-12-20 00:00:00","2018-01-20 00:00:00")
    ax.set_yticks(range(1,len(_lables)+1))
    ax.set_yticklabels(_lables,)
    ax.set_ylim(0,len(_lables)+1)
    _k_dots = []
    _r_dots = []
    for _dot in _dots:
        #print _dot[0],_dot[1]
        __dot = ax.scatter(_dot[0], _dot[1], marker=_dot[2], c=_dot[3])
        if _dot[3] == 'k':
            _k_dots.append(__dot)
        else:
            _r_dots.append(__dot)
    plt.xlabel(u'日期', fontsize=11)
    plt.ylabel(u'模块:测试次数', fontsize=11)
    plt.title(u'单元测试情况', fontsize=12)
    ax.grid(True)
    plt.legend([_k_dots[0], _r_dots[0]], [u"通过", u"未通过"])
    plt.subplots_adjust(left=0.28, bottom=0.09, top=0.96)

    _fn = 'pic/%s-compscore.png' % time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
    if not _test_mod:
        plt.savefig(_fn, dpi=120)
    else:
        plt.show()
    return _fn

if __name__ == '__main__':

    _test_mod = True

    db = MySQLdb.connect(host="47.93.192.232", user="root", passwd="sw64419", db="nebula", charset='utf8')
    cur = db.cursor()

    doJinkinsRec(cur)

    db.close()
