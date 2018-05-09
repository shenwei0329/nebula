#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# 任务计划跟踪器
# ==============
# 2017年12月6日@成都
#
#   2018年2月8日
#   ------------
#   + 里程碑Issue状态分布图，Y：状态；X：Issue。了解里程碑全局情况，以及变化“趋势”。
#       - Issue（story）总数；它们在待办、处理中、待测试、测试中、完成状态的分布情况，及其变化率（天）
#   + 里程碑Issue活动分布图，Y：Issue；X：时间。了解里程碑活动趋势。
#       - 基于“时标”展示Issue的活动情况（如：状态更改、时间要素（含预估，预分配、剩余、实际）更改）
#   + 里程碑挣值图，Y：成本；X：时间。了解“预算”执行情况。
#       - 基于“时标”展示以“预估”为基准的成本执行情况，主要指标：BCWS、ACWP和BCWP等，以表现出：
#           1）正常；2）执行延迟/超前；3）低于/超过预算；（注：在一个里程碑内，总预算按1:1线性关系分配到时标上）
#
#   2018年2月9日@成都
#   -----------------
#   更新报告内容：
#   一、要素：
#   1）里程碑：定义了时限（起始、结束）及目标（story）
#   2）目标（story）：定义了估计工时及需求点（UC）
#   3）任务：由目标（UC）分解，定义了具体的工作内容、状态、人员及估计用时、剩余时间和实际用时
#   4）活动：指任务的执行行为
#
#   二、（本里程碑内执行情况）报告内容：
#   1）工作分布：基于“时标”展示工作“活动”分布情况，如某任务状态迁移、时间更新等等
#   2）目标状态：基于“任务”展示其所处状态
#   3）目标执行：基于“时标”展示目标迁移“趋势”
#   3）成本执行：基于“时标”展示预算成本的实际执行情况（挣值分析）
#
#   2018年3月2日@成都
#   -----------------
#   应考虑：
#   1）项目执行的总体情况
#   2）项目挣值情况
#


import MySQLdb
import sys
import json
import time
import os
import datetime
import types
import doPie
import doHour
import doBox
from docx.enum.text import WD_ALIGN_PARAGRAPH
import crWord
import showJinkinsRec
import showJinkinsCoverage
import mongodb_class
import jira_class_epic
import re
import pandas as pd

reload(sys)
sys.setdefaultencoding('utf-8')

from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']

sp_name = [u'杨飞', u'吴昱珉', u'王学凯', u'许文宝',
           u'饶定远', u'金日海', u'沈伟', u'谭颖卿',
           u'吴丹阳', u'查明', u'柏银', u'崔昊之']

"""人天成本"""
CostDay = 1000.
CostHour = CostDay/8.
# 一个point等于4个工时
COST_ONE_POINT = 4

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

    if title_lvl == 1:
        Topic_lvl_number = 0
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
    _sql = 'select count(*) from jira_task_t where issue_type="story"'
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
            _like_str = "%s%%%s" % (_topic[0], _name[0])
            #print _like_str
            """在Jira中查找满足任务名称的项目"""
            _sql = u'select issue_id,summary,users,issue_status from jira_task_t where ' \
                   u'summary like "%%%s%%" and  issue_type="story"' % _like_str
            _tasks = doSQL(cur, _sql)
            for _task in _tasks:
                if not _kv.has_key(_task[0]):
                    _kv[_task[0]] = []
                (_kv[_task[0]]).append([_like_str,_task[1],_task[2],_task[3]])
                _n += 1

    return _kv, _m, _n


def collectBurnDownData(mongo_db, sprints, current_sprint, issue_filter=None):

    if type(sprints) != types.NoneType:
        _status_trans = {u"TO DO": 'waiting',
                         u"IN PROGRESS": 'doing',
                         u"待测试": 'wait_testing',
                         u"测试中": 'testing',
                         u"DONE": 'done'}

        Dots = []
        SpentTimes = []
        for _sprint in sprints:

            if current_sprint not in _sprint['name']:
                continue

            _data = {"sprint":[_sprint['startDate'], _sprint['endDate'], _sprint['state']]}
            _spent_time_dot = {"sprint":[_sprint['startDate'], _sprint['endDate'], _sprint['state']]}
            """
            _search = {"sprint": _sprint["name"],
                       "issue_type": u'任务',
                       "$and": [{"updated": {"$gte": _sprint['startDate']}},
                                {"updated": {"$lte": _sprint['endDate']}}]}
            '$regex' : ".*atmosphere.*"
            """
            _search = {"sprint": {'$regex': ".*%s.*" % _sprint["name"]},
                       "issue_type": u'任务'}
            """
            _tot_count = mongo_db.handler('issue', 'count', _search)
            print '---> get_count: ', mongo_db.get_count('issue', _search)
            """

            """获取本sprint内所有issue列表"""
            _cur = mongo_db.handler('issue', 'find', _search)
            tot_issue = {}
            tot_issue_spent_time = {}
            tot_issue_org_time = {}
            _tot_count = 0
            _tot_org_time = 0
            for _i in _cur:
                if issue_filter is not None:
                    if issue_filter in _i['summary']:
                        continue
                tot_issue[_i['issue']] = u'待办'
                tot_issue_spent_time[_i['issue']] = 0
                tot_issue_org_time[_i['issue']] = 0
                _tot_count += 1
                if type(_i['org_time']) is not types.NoneType:
                    _tot_org_time += int(_i['org_time'])/1800

            print "_tot_issue.len = ", len(tot_issue)

            # print "Total: %d" % _tot_count
            _data['count'] = _tot_count
            _spent_time_dot['count'] = _tot_org_time
            _data['dots'] = []
            _spent_time_dot['dots'] = []
            _date_index = pd.date_range(start=_sprint['startDate'], end=_sprint['endDate'], freq='1D').date
            for _date in _date_index:
                _task_count = _tot_count
                if _date > datetime.datetime.now().date():
                    break
                # print _date,"--->",
                """ 重置满足时间窗口的 issue 集的状态 """

                """
                【历史】：用log表做历史回顾。
                
                _search = {
                    "key": "status",
                    "_id": {"$lte": mongo_db.objectIdWithTimestamp(
                        "%s" % (_date + datetime.timedelta(days=1)))}
                }
                _tot_issue = tot_issue
                _cur = mongo_db.handler('log', 'find', _search)
                """

                """用changelog做历史回顾"""
                _search = {
                    "field": {"$in": ["status", "timespent", "timeoriginalestimate"]},
                    "date": {"$lte": "%s" % (_date + datetime.timedelta(days=1))}
                }
                _tot_issue = tot_issue
                """按升序查找"""
                _cur = mongo_db.handler('changelog', 'find', _search)
                for _i in _cur:
                    if _i['issue'] in _tot_issue:
                        if _i['field'] == 'status':
                            _tot_issue[_i['issue']] = _i['new']
                        elif _i['field'] == 'timespent':
                            tot_issue_spent_time[_i['issue']] = _i['new']
                        else:
                            tot_issue_org_time[_i['issue']] = _i['new']

                _time = 0
                for _i in tot_issue_spent_time:
                    _time += int(tot_issue_spent_time[_i])/1800
                _spent_time_dot['dots'].append(["%s" % _date, _time, 'spent'])
                _time = 0
                for _i in tot_issue_org_time:
                    _time += int(tot_issue_org_time[_i])/1800
                _spent_time_dot['dots'].append(["%s" % _date, _time, 'org'])

                for _status in [u'DONE', u'测试中', u'待测试', u'IN PROGRESS']:
                    """ 统计此窗口内 各个状态 issue 的总数 """
                    _count = 0
                    for _i in _tot_issue:
                        if _tot_issue[_i].upper() == _status:
                            _count += 1
                    _data[_status_trans[_status]] = _count
                    _task_count -= _count
                    print _status, '_tot_issue.len: ', len(_tot_issue), '_count:', _count, '_task_count:', _task_count
                    _data['dots'].append(["%s" % _date, _task_count, _status_trans[_status]])
                _data[_status_trans[u"TO DO"]] = _task_count
                print "---"
            Dots.append(_data)
            SpentTimes.append(_spent_time_dot)
        return Dots, SpentTimes
    return None, None


def collectBurnDownDataByLandmark(mongo_db, landmark):

    _status_trans = {u"TO DO": 'waiting',
                     u"IN PROGRESS": 'doing',
                     u"待测试": 'wait_testing',
                     u"测试中": 'testing',
                     u"DONE": 'done'}

    Dots = []
    SpentTimes = []

    _data = {"sprint": [landmark['startDate'], landmark['endDate'], 'ACTIVE']}
    _spent_time_dot = {"sprint": [landmark['startDate'], landmark['endDate'], 'ACTIVE']}

    _search = {"landmark": landmark["name"], "issue_type": u'任务'}
    """获取本里程碑内所有issue列表"""
    _cur = mongo_db.handler('issue', 'find', _search)
    tot_issue = {}
    tot_issue_spent_time = {}
    tot_issue_org_time = {}
    _tot_count = 0
    _tot_org_time = 0
    for _i in _cur:

        tot_issue[_i['issue']] = _i['status']
        tot_issue_spent_time[_i['issue']] = 0
        tot_issue_org_time[_i['issue']] = 0
        _tot_count += 1
        if type(_i['org_time']) is not types.NoneType:
            _tot_org_time += int(_i['org_time']) / 1800

    print "_tot_issue.len = ", len(tot_issue)

    # print "Total: %d" % _tot_count
    _data['count'] = _tot_count
    _spent_time_dot['count'] = _tot_org_time
    _data['dots'] = []
    _spent_time_dot['dots'] = []

    """ 观察的是在本里程碑内的行为（状态更改、工时等）
        问题：在进入本里程碑前有的任务就已经完成了。
    """
    _date_index = pd.date_range(start=landmark['startDate'], end=landmark['endDate'], freq='1D').date
    for _date in _date_index:
        _task_count = _tot_count
        if _date > datetime.datetime.now().date():
            break
        # print _date,"--->",
        """ 重置满足时间窗口的 issue 集的状态 """

        """用changelog做历史回顾"""
        _search = {
            "field": {"$in": ["status", "timespent", "timeoriginalestimate"]},
            "date": {"$lte": "%s" % (_date + datetime.timedelta(days=1))}
        }
        _tot_issue = tot_issue
        """按升序查找"""
        _cur = mongo_db.handler('changelog', 'find', _search).sort([('date', 1)])
        for _i in _cur:
            if _i['issue'] in _tot_issue:
                if _i['field'] == 'status':
                    _tot_issue[_i['issue']] = _i['new']
                elif _i['field'] == 'timespent':
                    tot_issue_spent_time[_i['issue']] = _i['new']
                else:
                    tot_issue_org_time[_i['issue']] = _i['new']

        _time = 0
        for _i in tot_issue_spent_time:
            if type(tot_issue_spent_time[_i]) is not types.NoneType:
                _time += int(tot_issue_spent_time[_i]) / 1800
        _spent_time_dot['dots'].append(["%s" % _date, _time, 'spent'])
        _time = 0
        for _i in tot_issue_org_time:
            if type(tot_issue_org_time[_i]) is not types.NoneType:
                _time += int(tot_issue_org_time[_i]) / 1800
        _spent_time_dot['dots'].append(["%s" % _date, _time, 'org'])

        for _status in [u'DONE', u'测试中', u'待测试', u'IN PROGRESS']:
            """ 统计此窗口内 各个状态 issue 的总数 """
            _count = 0
            for _i in _tot_issue:
                if _tot_issue[_i].upper() == _status:
                    _count += 1
            _data[_status_trans[_status]] = _count
            _task_count -= _count
            print _status, '_tot_issue.len: ', len(_tot_issue), '_count:', _count, '_task_count:', _task_count
            _data['dots'].append(["%s" % _date, _task_count, _status_trans[_status]])
        _data[_status_trans[u"TO DO"]] = _task_count
        print "---"
    Dots.append(_data)
    SpentTimes.append(_spent_time_dot)
    return Dots, SpentTimes


def collectBurnDownDataByTask(mongo_db, landmark):

    _status_trans = {u"TO DO": 'waiting',
                     u"IN PROGRESS": 'doing',
                     u"待测试": 'wait_testing',
                     u"测试中": 'testing',
                     u"DONE": 'done'}

    Dots = []
    SpentTimes = []

    _data = {"sprint": [landmark['startDate'], landmark['endDate'], 'ACTIVE']}
    _spent_time_dot = {"sprint": [landmark['startDate'], landmark['endDate'], 'ACTIVE']}

    tot_issue = {}
    tot_issue_spent_time = {}
    tot_issue_org_time = {}
    _tot_count = 0
    _tot_org_time = 0
    for _issue in landmark['task_list']:

        # print _issue
        _search = {"landmark": landmark["name"], "issue": _issue}
        # _search = {"issue": _issue}
        _i = mongo_db.handler('issue', 'find_one', _search)

        if _i is None:
            continue

        tot_issue[_i['issue']] = _i['status']
        tot_issue_spent_time[_i['issue']] = 0
        tot_issue_org_time[_i['issue']] = 0
        _tot_count += 1
        if type(_i['org_time']) is not types.NoneType:
            _tot_org_time += int(_i['org_time']) / 1800

    print "_tot_issue.len = ", len(tot_issue)

    # print "Total: %d" % _tot_count
    _data['count'] = _tot_count
    _spent_time_dot['count'] = _tot_org_time
    _data['dots'] = []
    _spent_time_dot['dots'] = []

    """ 观察的是在本里程碑内的行为（状态更改、工时等）
        问题：在进入本里程碑前有的任务就已经完成了。
    """
    _date_index = pd.date_range(start=landmark['startDate'], end=landmark['endDate'], freq='1D').date
    for _date in _date_index:
        _task_count = _tot_count
        if _date > datetime.datetime.now().date():
            break
        # print _date,"--->",
        """ 重置满足时间窗口的 issue 集的状态 """

        """用changelog做历史回顾"""
        _search = {
            "field": {"$in": ["status", "timespent", "timeoriginalestimate"]},
            "date": {"$lte": "%s" % (_date + datetime.timedelta(days=1))}
        }
        _tot_issue = tot_issue
        """按升序查找"""
        _cur = mongo_db.handler('changelog', 'find', _search).sort([('date', 1)])
        for _i in _cur:
            if _i['issue'] in _tot_issue:
                if _i['field'] == 'status':
                    _tot_issue[_i['issue']] = _i['new']
                elif _i['field'] == 'timespent':
                    tot_issue_spent_time[_i['issue']] = _i['new']
                else:
                    tot_issue_org_time[_i['issue']] = _i['new']

        _time = 0
        for _i in tot_issue_spent_time:
            if type(tot_issue_spent_time[_i]) is not types.NoneType:
                _time += int(tot_issue_spent_time[_i]) / 1800
        _spent_time_dot['dots'].append(["%s" % _date, _time, 'spent'])
        _time = 0
        for _i in tot_issue_org_time:
            if type(tot_issue_org_time[_i]) is not types.NoneType:
                _time += int(tot_issue_org_time[_i]) / 1800
        _spent_time_dot['dots'].append(["%s" % _date, _time, 'org'])

        for _status in [u'DONE', u'测试中', u'待测试', u'IN PROGRESS']:
            """ 统计此窗口内 各个状态 issue 的总数 """
            _count = 0
            for _i in _tot_issue:
                if _tot_issue[_i].upper() == _status:
                    _count += 1
            _data[_status_trans[_status]] = _count
            _task_count -= _count
            print _status, '_tot_issue.len: ', len(_tot_issue), '_count:', _count, '_task_count:', _task_count
            _data['dots'].append(["%s" % _date, _task_count, _status_trans[_status]])
        _data[_status_trans[u"TO DO"]] = _task_count
        print "---"
    Dots.append(_data)
    SpentTimes.append(_spent_time_dot)
    return Dots, SpentTimes


def calIssuePassCount(mongodb, issue_name):
    """
    计算指定issue的测试次数
    :param mongodb: 数据源
    :param issue_name: 处理对象
    :return: 测试次数
    """
    return mongodb.handler("changelog", "find", {"issue": issue_name,
                                                 "field": 'status',
                                                 "new": "In Progress"}).count()


def Performance(mongodb, landmark):
    """
    计算本阶段所投入资源的工作绩效。
    1）计算“个人”绩效指标
        1）工作情况：效率=工时/任务；已完成任务数，N质量；在执行的任务数（含正在做的，待测试的）。
        2）职级评估：计算执行人的 n 工时/point。
    2）评定“个人”分值，并排序
    3）对“个人”职级水平进行评估
    :param mongodb：数据源
    :param landmark：当前 里程碑
    :return: 总体绩效情况
    """
    _search = {"issue_type": u"任务",
               # "sprint": {'$regex': ".*%s.*" % current_sprint.split(' ')[0]},
               "landmark": landmark,
               "status": {'$in': [u'完成', u'处理中', u'待测试', u'测试中']},
               }
    _users = {}
    _cur = mongodb.handler('issue', 'find', _search)
    _tot_task_count = 0
    for _issue in _cur:
        if _issue['users'] is None:
            continue
        if _issue['users'] not in _users:
            _users[_issue['users']] = {"done": 0,
                                       "done_org_time": 0,
                                       "doing": 0,
                                       "org_time": 0,
                                       "spent_time": 0,
                                       "pass": 0}
        if _issue['status'] == u'完成':
            _users[_issue['users']]['done'] += 1
            if type(_issue['org_time']) is not types.NoneType:
                _users[_issue['users']]['done_org_time'] += _issue['org_time'] / 1800
        else:
            _users[_issue['users']]['doing'] += 1
        if type(_issue['org_time']) is not types.NoneType:
            _users[_issue['users']]['org_time'] += _issue['org_time']/1800
            _tot_task_count += (_issue['org_time'] / 1800)
        if type(_issue['spent_time']) is not types.NoneType:
            _users[_issue['users']]['spent_time'] += _issue['spent_time']/1800
        _users[_issue['users']]['pass'] += calIssuePassCount(mongodb, _issue['issue'])

    return _users, _tot_task_count


def get_issue_by_sprint(mongodb, sprint):
    """
    获取指定 sprint 的Issue数据
    :param mongodb: 数据源
    :param sprint: 指定的 sprint
    :return:
    """
    print "--> get_issue_by_sprint: ",sprint[0]
    _story = mongodb.handler("issue", "find", {'issue_type': "story",
                                               "sprint": {'$regex': ".*%s.*" % sprint[0]}})
    return get_issue_public(mongodb, _story)


def get_issue_by_landmark(mongodb, landmark):
    """
    获取指定里程碑的Issue数据
    :param mongodb: 数据源
    :param landmark: 指定的里程碑
    :return:
    """
    print "--> get_issue_by_landmark: ", landmark
    _story = mongodb.handler("issue", "find", {'issue_type': "story",
                                               "landmark": landmark})
    return get_issue_public(mongodb, _story)


def get_issue_public(mongodb, _story):

    # 获取本里程碑内所有任务
    _task_list = []
    _story_task_list = {}
    _story_points = {}
    _max_cost = 0
    for _st in _story:
        _id = _st['issue']
        _link = mongodb.handler("issue_link", "find", {"issue": _id})
        if _id not in _story_task_list:
            _story_task_list[_id] = {'org_time': 0, 'agg_time': 0, 'spent_time': 0}
            if type(_st['point']) is not types.NoneType:
                _story_points[_id] = int(_st['point']) * COST_ONE_POINT * 3600
            else:
                print "!!! ", _id, " no points be defined"
                _story_points[_id] = 0
            if _max_cost < _story_points[_id]:
                _max_cost = _story_points[_id]
        for _l in _link:
            for _t in _l[_id]:
                if _t not in _task_list:
                    _task_list.append(_t)
                    _logs = mongodb.handler("issue", "find", {"issue": _t})
                    for _log in _logs:
                        if type(_log['org_time']) is types.IntType:
                            _v = _log['org_time']
                        else:
                            _v = 0
                        _story_task_list[_id]['org_time'] += _v
                        if type(_log['spent_time']) is types.IntType:
                            _v = _log['spent_time']
                        else:
                            _v = 0
                        _story_task_list[_id]['spent_time'] += _v
                        if type(_log['agg_time']) is types.IntType:
                            _v = _log['agg_time']
                        else:
                            _v = 0
                        _story_task_list[_id]['agg_time'] += _v

                    if _max_cost < _v:
                        _max_cost = _v

        if _max_cost < _story_task_list[_id]['org_time']:
            _max_cost = _story_task_list[_id]['org_time']
        _story_task_list[_id]['agg_time'] += _story_task_list[_id]['spent_time']
        if _max_cost < _story_task_list[_id]['agg_time']:
            _max_cost = _story_task_list[_id]['agg_time']

    return _task_list, _story_task_list, _story_points, _max_cost


def getWorkActionChart(mongodb, TaskList, who=None):
    """
    获取 指定个人或集体的 工作行为的图示
    :param mongodb: 数据源mongodb
    :param TaskList: 完成的任务issue列表
    :param who: 个人
    :return: 图示的文件路径
    """

    _dots = []
    _issues = []
    _y = 1
    for _t in TaskList:
        if who is None:
            _log = mongodb.handler("changelog", "find", {"issue": _t,
                                                          "field": {"$in": ['timeoriginalestimate',
                                                                            'timeestimate',
                                                                            'timespent',
                                                                            'WorklogTimeSpent',
                                                                            'status',
                                                                            u"bug产生人",
                                                                            'resolution']}})
        else:
            _log = mongodb.handler("changelog", "find", {"issue": _t,
                                                         "author": who,
                                                         "field": {"$in": ['timeoriginalestimate',
                                                                           'timeestimate',
                                                                           'timespent',
                                                                           'WorklogTimeSpent',
                                                                           'status',
                                                                           u"bug产生人",
                                                                           'resolution']}})

        _count = 0
        for _l in _log:
            _dots.append([_l["date"], _y, _l["field"]])
            _count += 1
        if _count > 0:
            _issues.append(_t)
            _y += 1
    if who is None:
        _figsize = [10, 12]
    else:
        _figsize = [10, 6]
    if len(_dots) > 0:
        return doBox.doIssueAction(_issues, _dots, figsize=_figsize)
    return None


def main(project="PRD-2017-PROJ-00003", project_alias='FAST', week_end=False, landmark_id=None):
    """
    项目跟踪报告生成器
    :param project: 项目编号
    :param project_alias: 项目别名，如FAST、HUBBLE...
    :param week_end：周末？
    :param landmark_id：里程碑ID
    :return: 报告（word、pdf）
    """

    global doc

    """创建word文档实例
    """
    doc = crWord.createWord()
    """写入"主题"
    """
    doc.addHead(u'产品%s项目计划跟踪报告' % project_alias, 0, align=WD_ALIGN_PARAGRAPH.CENTER)

    """MySQL数据库
    """
    db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    # db = MySQLdb.connect(host="172.16.101.117",user="root",passwd="123456",db="nebula",charset='utf8')
    cur = db.cursor()

    """mongoDB数据库
    """
    mongo_db = mongodb_class.mongoDB(project_alias)

    # 获取里程碑信息
    _landmark = mongo_db.handler("project", "find", {'id': landmark_id})[0]['version'].replace('^', '.')
    _startDate = mongo_db.handler("project", "find", {'id': landmark_id})[0]['startDate']
    _endDate = mongo_db.handler("project", "find", {'id': landmark_id})[0]['releaseDate']

    print _landmark
    """Jira类
    """
    jira = jira_class_epic.jira_handler(project_alias)
    sprints = jira.get_sprints()

    cur_sprint, next_sprint = jira.get_current_sprint()
    current_sprint = cur_sprint[0]
    sprint_start_date = cur_sprint[1]
    sprint_end_date = cur_sprint[2]
    print u"%s 从 %s 至 %s" % (current_sprint, sprint_start_date, sprint_end_date)

    # 获取本里程碑内story
    # _story = mongo_db.handler("issue", "find", {'issue_type': "story", "landmark": u"%s" % _landmark})
    # _task_list, _story_task_list, _story_points, _max_cost = get_issue_by_sprint(mongo_db, cur_sprint)
    _task_list, _story_task_list, _story_points, _max_cost = get_issue_by_landmark(mongo_db, _landmark)


    # _burndown_dots, _timeburndown_dots = collectBurnDownData(mongo_db, sprints, current_sprint)
    """
    _burndown_dots, _timeburndown_dots = collectBurnDownDataByLandmark(mongo_db,
                                                                       {'name': _landmark,
                                                                        'startDate': _startDate,
                                                                        'endDate': _endDate})
    """
    print _task_list
    _burndown_dots, _timeburndown_dots = collectBurnDownDataByTask(mongo_db,
                                                                   {'name': _landmark,
                                                                    'startDate': _startDate,
                                                                    'endDate': _endDate,
                                                                    'task_list': _task_list})
    _burndown_fn = doBox.BurnDownChart(_burndown_dots)
    _timeburndown_fn = doBox.TimeBurnDownChart(_timeburndown_dots)
    """
    _burndown_pd_dots = collectBurnDownData(mongo_db, sprints, current_sprint, issue_filter=u'项目入侵')
    _burndown_pd_fn = doBox.BurnDownChart(_burndown_pd_dots)
    """

    _print('>>> 报告生成日期【%s】 <<<' % time.ctime(), align=WD_ALIGN_PARAGRAPH.CENTER)

    """报告结论"""
    _results = []

    # 获取Issue的summary
    _issue_ext_list = []
    _res = mongo_db.handler("issue", "find", {"issue_type":"story", "summary": re.compile(r'.入侵.*?')})
    for _r in _res:
        _issue_ext_list.append(_r["issue"])

    # 获取任务的变化情况
    _fn_issue_action = getWorkActionChart(mongo_db, _task_list)

    """2018.3.28：按个人显示工作行为
    """
    _fn_issue_action_personal = {}
    _sql = 'select MM_XM from member_t where MM_ZT=1'
    _res = doSQL(cur, _sql)
    for _row in _res:
        if u"%s" % _row[0] in sp_name:
            continue
        _fn_issue_action_personal[_row[0]] = getWorkActionChart(mongo_db, _task_list, _row[0])

    # 获取任务状态
    _dots = []
    _status = {u"待办": 1, u"处理中": 2, u"待测试": 3, u"测试中": 4, u"完成": 5}
    _x = 1
    _dots_s = {}
    _issue_error_rate = {}
    for _t in _task_list:
        """
        获取未通过测试的Issue：
                {field:'status', new:"In Progress", old:{$ne: 'To Do'}} （排除第一次）
                 或者
                {field:'status', new:"In Progress"}（包含第一次）
        """
        # _dots_s[_t] = mongo_db.handler("log", "find", {"issue_id": _t, "key": "status", "new": u"处理中"}).count()
        _dots_s[_t] = mongo_db.handler("changelog", "find", {"issue": _t,
                                                             "field": 'status',
                                                             "new": "In Progress"}).count()
        _is = mongo_db.handler("issue", "find", {"issue": _t})
        for _i in _is:
            if _i['status'] in _status:
                if _t not in _issue_ext_list:
                    _dots.append([_x, _status[_i['status']], 'o', 'k'])
                else:
                    _dots.append([_x, _status[_i['status']], 'v', 'r'])
            _issue_error_rate[_t] = [u"%s" % _i['summary'], _dots_s[_t]]
        _x += 1
    print _task_list
    _fn_issue_status = doBox.doIssueStatus(u"任务执行状态分布图", u"任务", _task_list, _dots, _dots_s)

    # 获取目标状态
    _dots = []
    _x = 1
    _issues = []
    _story = mongo_db.handler("issue", "find",
                              {'issue_type': "story",
                               # "summary": {"$regex": ".*UC.*"},
                               # "sprint": {'$regex': ".*%s.*" % current_sprint}
                               'landmark': _landmark
                               })
    _dots_s = {}
    for _st in _story:
        _id = _st['issue']
        _is = mongo_db.handler("issue", "find", {"issue": _id})
        for _i in _is:
            if _i['status'] in _status:
                if _id not in _issue_ext_list:
                    _dots.append([_x, _status[_i['status']], 'o', 'k'])
                    _dots_s[_id] = 1
                else:
                    _dots.append([_x, _status[_i['status']], 'v', 'r'])
                    _dots_s[_id] = 3
        _issues.append(_id)
        _x += 1
    _fn_story_status = doBox.doIssueStatus(u"本期目标状态分布图", u"目标（story）", _issues, _dots, _dots_s)

    # 生成预算执行信息
    _dots = []
    _x = 1
    _issues = []
    # _story = mongo_db.handler("issue", "find", {'issue_type': "story", "landmark": u"%s" % _landmark})
    _story = mongo_db.handler("issue", "find", {'issue_type': "story",
                                                # "summary": {"$regex": ".*UC.*"},
                                                # "sprint": {'$regex': ".*%s.*" % current_sprint}})
                                                "landmark": _landmark})
    _tot_points = 0
    _tot_agg_times = 0
    _tot_spent_times = 0
    _sn = 1
    for _st in _story:
        _dots.append([_x, _story_points[_st['issue']], 'H', 'g'])
        _tot_points += _story_points[_st['issue']]
        _str = ""

        if _story_points[_st['issue']] == 0:
            _str = u"%d） %s：%s，未分配预算。" % (_sn, _st['issue'], _st['summary'])
            _sn += 1

        # _dots.append([_x, _story_task_list[_st['issue']]['org_time'], 'x', 'g'])
        _dots.append([_x, _story_task_list[_st['issue']]['org_time'], 's', 'b'])
        """
        if _story_task_list[_st['issue']]['org_time'] == 0:
            if len(_str) == 0:
                _str = u"● 目标【%s】包含未定义工作量的任务。" % _st['issue']
            else:
                _str += u"它包含未定义工作量的任务。"
        """
        _tot_agg_times += _story_task_list[_st['issue']]['org_time']
        _dots.append([_x, _story_task_list[_st['issue']]['spent_time'], '^', 'r'])
        _tot_spent_times += _story_task_list[_st['issue']]['spent_time']
        _issues.append(_st['issue'])

        if len(_str) > 0:
            _results.append([_str, (255, 0, 0)])

        _x += 1

    """ 挣值分析：
        1）预算指标：基于story定义的point值
        2）执行情况：基于spent_time确定的已花费情况
        3）偏差：执行与预算的+/-偏差
        4）任务的状态
    """
    _fn_cost = doBox.doIssueCost(u"本期目标成本分布图", u"目标（story）", _issues, _dots, _max_cost)

    _sql = 'select PJ_XMMC,PJ_XMFZR,PJ_KSSJ,PJ_JSSJ,PJ_XMJJ,PJ_XMYS from project_t where PJ_XMBH="%s"' % project
    _res = doSQL(cur, _sql)
    if _res is None or len(_res) == 0:
        print("\n\tErr: Invalid number of project: %s)" % project)

    _print(u"项目基本信息", title=True, title_lvl=1)

    _print(u'项目名称：%s' % _res[0][0])
    _print(u'项目编号：%s' % project)
    _print(u'项目负责人：%s' % _res[0][1])
    _print(u'项目起止日期：%s 至 %s' % (_res[0][2], _res[0][3]))
    _print(u'项目预算（工时成本）：%s 万元' % _res[0][5])
    _print(u'项目功能简介：%s' % _res[0][4])
    _print(u'里程碑：%s，从 %s 到 %s' % (_landmark, _startDate, _endDate))
    # _print(u'上一个阶段：%s，从 %s 至 %s' % (next_sprint[0], next_sprint[1], next_sprint[2]))
    _print(u'当前阶段：%s，从 %s 至 %s' % (current_sprint, sprint_start_date, sprint_end_date))

    """需要在此插入语句"""
    _print(u"情况总览", title=True, title_lvl=1)

    _my_paragrap = _print(u"本里程碑的基本情况", title=True, title_lvl=1)
    """本里程碑的情况"""
    _search = {"issue_type": 'story',
               # "summary": {"$regex": ".*UC.*"},
               # "sprint": {"$regex": ".*%s.*" % current_sprint}}
               "landmark": _landmark}
    _tot_count = mongo_db.handler('issue', 'count', _search)
    __search = {"issue_type": 'story',
                # "summary": {"$regex": ".*UC.*"},
                "status": "完成",
                # "sprint": {"$regex": ".*Sprint 5.*"}
                "landmark": _landmark}
    _done_count = mongo_db.handler('issue', 'count', __search)
    _print(u"本阶段共有 %d 个功能点，已完成 %d 个，完成率 %0.2f%%，明细如下：" % (
        _tot_count, _done_count, float((_done_count*100)/_tot_count)
    ))
    doc.addTable(1, 4, col_width=(7, 1, 7, 1))
    _title = (('text', u'功能名称'), ('text', u'状态'),
              ('text', u'功能名称'), ('text', u'状态'))
    doc.addRow(_title)
    _cur = mongo_db.handler('issue', 'find', _search)
    _idx = 0
    _text = ()
    for _issue in _cur:
        _text += (('text', u"%s" % _issue['summary'].replace('【UC】','')),
                  ('text', u"%s" % _issue['status']))
        if _idx > 0:
            doc.addRow(_text)
            _text = ()
            _idx = 0
        else:
            _idx += 1
    doc.setTableFont(8)
    _print("")

    _print(u"个人绩效指标", title=True, title_lvl=1)
    _users, _tot_task_count = Performance(mongo_db, _landmark)
    _print(u"本阶段执行过程中研发团队个人（共%d人）综合情况如下：" % len(_users))
    doc.addTable(1, 5, col_width=(3, 2, 2, 2, 2))
    _title = (('text', u'人员'),
              ('text', u'完成率'),
              ('text', u'消耗率'),
              ('text', u'贡献率'),
              ('text', u'质量系数'))
    doc.addRow(_title)
    for _user in _users:
        if _user in sp_name:
            continue
        _u = float(_users[_user]['done_org_time'])*100./float(_users[_user]['org_time'])
        _miu = float(_users[_user]['spent_time'])*100./float(_users[_user]['org_time'])
        _cr = float(_users[_user]['org_time'])*100./float(_tot_task_count)
        _q = float(_users[_user]['pass'])/_cr
        _text = (('text', _user),
                 ('text', "%0.2f" % _u),
                 ('text', "%0.2f" % _miu),
                 ('text', "%0.2f" % _cr),
                 ('text', "%0.2f" % _q)
                 )
        print "---> ", _text
        doc.addRow(_text)
    doc.setTableFont(8)
    _print("【说明】：1）任务完成率：完成任务量的占比；2）消耗率：已消耗工时的占比；"
           "3）贡献率：承接任务量的占比；4）质量系数：返工数/贡献率。")

    _print(u"非计划类事务情况", title=True, title_lvl=1)
    _print(u"本阶段执行过程中插入了以下“外来”的事务：")
    _i = 1
    _tot_cost = 0
    _res = mongo_db.handler("issue", "find", {"issue_type": u"story",
                                              # "sprint": {'$regex': ".*%s.*" % current_sprint},
                                              "landmark": _landmark,
                                              # "summary": re.compile(r'.入侵.*?')
                                              "summary": {'$regex': ".*入侵.*"}
                                              })
    for _issue in _res:
        if type(_issue['point']) is types.NoneType or _issue['point'] <= 0:
            continue
        _print(u"%d）%s：%s，预估投入成本%d（工时）" % (
                _i,
                _issue['issue'],
                _issue['summary'].replace(u"【项目入侵】",""),
                int(_issue['point']) * COST_ONE_POINT))
        _i += 1
        _tot_cost += int(_issue['point']) * COST_ONE_POINT
    _print(u"计划外事务的总投入（估算） %d 个工时。" % _tot_cost)

    doc.addPageBreak()

    _print(u"过程情况", title=True, title_lvl=1)
    _print(u'1）单元测试情况：')
    _fn, _error_rate, _avg_cnt = showJinkinsRec.doJinkinsRec(cur, project_alias)
    if _fn is None:
        _print(u"无。")
    else:
        doc.addPic(_fn, sizeof=6.2)
        _print(u'【图例说明】：数据采自Jenkins系统，以展示项目中每个模块的单元测试情况。')
        doc.addPageBreak()

        """ 增加一个列表：近期出错率高的模块
        """
        _print(u'按出错率排序（前十名）：')
        doc.addTable(1, 3, col_width=(5, 2, 2))
        _title = (('text', u'模块名'),
                  ('text', u'测试次数'),
                  ('text', u'出错率%'))
        doc.addRow(_title)
        _i = 0
        for _err in sorted(_error_rate, key=lambda x: -int(_error_rate[x][1]*100.)):
            if _error_rate[_err][0] > _avg_cnt:
                _text = (('text', u'%s' % _err),
                         ('text', '%d' % _error_rate[_err][0]),
                         ('text', '%0.2f' % _error_rate[_err][1])
                         )
                doc.addRow(_text)
                _i += 1
                if _i >= 10:
                    break
        doc.setTableFont(8)

        _print(u'按测试次数排序（前十名）：')
        doc.addTable(1, 3, col_width=(5, 2, 2))
        _title = (('text', u'模块名'),
                  ('text', u'测试次数'),
                  ('text', u'出错率%'))
        doc.addRow(_title)
        _i = 0
        for _err in sorted(_error_rate, key=lambda x: -_error_rate[x][0]):
            if _error_rate[_err][0] > _avg_cnt:
                _text = (('text', u'%s' % _err),
                         ('text', '%d' % _error_rate[_err][0]),
                         ('text', '%0.2f' % _error_rate[_err][1])
                         )
                doc.addRow(_text)
                _i += 1
                if _i >= 10:
                    break
        doc.setTableFont(8)

        _print(u'按稳定性排序（前十名）：')
        doc.addTable(1, 3, col_width=(5, 2, 2))
        _title = (('text', u'模块名'),
                  ('text', u'测试次数'),
                  ('text', u'出错率%'))
        doc.addRow(_title)
        _i = 0
        for _err in sorted(_error_rate, key=lambda x: -int(float(_error_rate[x][0])*(1.-_error_rate[x][1]/100.))):
            if _error_rate[_err][0] > _avg_cnt:
                _text = (('text', u'%s' % _err),
                         ('text', '%d' % _error_rate[_err][0]),
                         ('text', '%0.2f' % _error_rate[_err][1])
                         )
                doc.addRow(_text)
                _i += 1
                if _i >= 10:
                    break
        doc.setTableFont(8)

        doc.addPageBreak()

    _print(u'2）单元测试覆盖率：')
    _fn = showJinkinsCoverage.doJinkinsCoverage(cur, project_alias)
    if _fn is None:
        _print(u"无。")
    else:
        doc.addPic(_fn, sizeof=5.8)
        _print(u'【图例说明】：数据采自Jenkins系统，以展示项目中每个模块的单元测试覆盖率。')

    _print(u"计划跟踪", title=True, title_lvl=1)

    #   1）活动分布：基于“时标”展示工作“活动”分布情况，如某任务状态迁移、时间更新等等
    _print(u"活动分布", title=True, title_lvl=2)
    doc.addPic(_fn_issue_action, sizeof=6.2)
    _print(u'【图例说明】：基于“时标”展示工作“活动”分布情况，如某任务状态迁移、时间更新等等。')
    _print("")

    _print(u"活动分布分解", title=True, title_lvl=3)
    for _personal in _fn_issue_action_personal:
        if _fn_issue_action_personal[_personal] is None:
            continue
        _print(u"%s的活动分布" % _personal, title=True, title_lvl=4)
        doc.addPic(_fn_issue_action_personal[_personal], sizeof=5)
        _print("")

    doc.addPageBreak()

    #   2）目标状态：基于“任务”展示其所处状态
    _print(u"任务执行状态", title=True, title_lvl=2)
    _print(u"通过下图可直观了解在本里程碑内所有任务的当前执行情况。")
    doc.addPic(_fn_issue_status, sizeof=6)
    _print(u'【图例说明】：展示任务执行的状态分布情况。图中，圆点大小与任务被测试次数关联，'
           u'圆点越小则间接表示bug数也越少。')

    """ 增加一个表：目前出错率较高的 issue
    """
    _print(u'出错率较高的任务有：')
    doc.addTable(1, 3, col_width=(2, 5, 2))
    _title = (('text', u'Issue'),
              ('text', u'任务'),
              ('text', u'返工次数'))
    doc.addRow(_title)
    _j = 0
    for _i in sorted(_issue_error_rate, key=lambda x: -_issue_error_rate[x][1]):
        if _issue_error_rate[_i][1] > 1:
            _text = (('text', _i),
                     ('text', _issue_error_rate[_i][0]),
                     ('text', '%d' % _issue_error_rate[_i][1]))
            doc.addRow(_text)
        else:
            break
        _j += 1
        if _j > 10:
            break
    if _j == 0:
        _title = (('text', u'无'),
                  ('text', ""),
                  ('text', ""))
        doc.addRow(_title)
    doc.setTableFont(8)

    doc.addPageBreak()

    #   3）目标执行：基于“时标”展示目标迁移“趋势”
    _print(u"目标执行情况", title=True, title_lvl=2)
    _print(u"通过下图可直观了解在本里程碑内所有目标（功能点）的当前执行情况。")
    doc.addPic(_fn_story_status, sizeof=6)
    _print(u'【图例说明】：展示里程碑目标的状态分布情况。')

    #   4）成本执行：基于“时标”展示预算成本的实际执行情况（挣值分析）
    _print(u"成本执行", title=True, title_lvl=2)
    _print(u"● 计划预算总数：%d 【工时】" % (_tot_points/3600))
    _print(u"● 估计执行成本总数：%d 【工时】" % (_tot_agg_times/3600))
    _print(u"● 已执行成本总数：%d 【工时】" % (_tot_spent_times/3600))
    _print(u"通过下图可直观了解在本里程碑内所有目标（功能点）的预算执行情况。")
    doc.addPic(_fn_cost, sizeof=6)
    _print(u'【图例说明】：展示里程碑目标的预算执行情况。')

    #   5）燃尽图：基于“时标”展示每个里程碑任务的完成情况
    _print(u"任务执行情况", title=True, title_lvl=2)
    _print(u"本里程碑的任务燃尽情况如下：")
    """当前里程碑的情况"""
    _dot = _burndown_dots[-1]
    _print(u"● 任务总数：%d" % _dot["count"])
    _print(u"● 已完成的任务总数：%d" % _dot['done'])
    _print(u"● 在测的任务总数：%d" % _dot['testing'])
    _print(u"● 待测的任务总数：%d" % _dot['wait_testing'])
    _print(u"● 处理中的任务总数：%d" % _dot['doing'])
    _print(u"● 待办的任务总数：%d" % _dot['waiting'])
    doc.addPic(_burndown_fn, sizeof=5)
    _print(u'【图例说明】：图中的红线为“理想”的任务燃尽趋势。')

    _print("本阶段计划工时的燃尽情况：")
    doc.addPic(_timeburndown_fn, sizeof=5)
    _print(u'【图例说明】：图中的红线为“理想”的计划工时燃尽趋势。')

    doc_appendix = crWord.createWord()
    """写入"主题"
    """
    doc_appendix.addHead(u'【项目%s总体一览表】' % project_alias, 0, align=WD_ALIGN_PARAGRAPH.CENTER)

    """一览表：
        从 EPIC 开始向下列出其相关的 story 及其相关任务，项目包括：里程碑、状态、估计工时、实际工时、相关人
    """
    _tot_epic = 0
    _tot_story = 0
    _tot_done_story = 0
    _tot_task = 0
    _tot_done_task = 0
    doc_appendix.addTable(1, 8, col_width=(6, 6, 6, 3, 2, 2, 2, 2))
    _title = (('text', u'EPIC'), ('text', u'story'), ('text', u'任务'),
              ('text', u'里程碑'), ('text', u'状态'),
              ('text', u'估计工时'), ('text', u'执行工时'),
              ('text', u'执行人'))
    doc_appendix.addRow(_title)
    _search = {"issue_type": 'epic'}
    _cur = mongo_db.handler('issue', 'find', _search)
    for _issue in _cur:

        _tot_epic += 1
        _text = (('text', u'%s' % _issue['summary']),
                 ('text', ""),
                 ('text', ""),
                 ('text', ""),
                 ('text', ""),
                 ('text', ""),
                 ('text', ""),
                 ('text', "")
                 )
        doc_appendix.addRow(_text)
        _search = {"issue_type": 'story', "epic_link": _issue['issue']}
        _story_cur = mongo_db.handler('issue', 'find', _search)
        for _story in _story_cur:

            _tot_story += 1

            if _story['point'] is None:
                _point = 'null'
            else:
                _point = "%0.2f" % float(_story['point'])
            _text = (('text', ""),
                     ('text', u'%s' % _story['summary']),
                     ('text', ""),
                     ('text', u"%s" % _story['landmark']),
                     ('text', u"%s" % _story['status']),
                     ('text', _point),
                     ('text', ""),
                     ('text', u"%s" % _story['users'])
                     )
            doc_appendix.addRow(_text)
            if _story['status'] == u'完成':
                _tot_done_story += 1
            _search = {'issue': _story['issue']}
            _task_link = mongo_db.handler('issue_link', 'find_one', _search)

            if _task_link is None:
                continue

            for _task_id in _task_link[_story['issue']]:
                _search = {'issue': _task_id}
                _task = mongo_db.handler('issue', 'find_one', _search)
                _tot_task += 1
                if _task['status'] == u'完成':
                    _tot_done_task += 1
                if _task['org_time'] is None:
                    _org_time = "null"
                else:
                    _org_time = "%0.2f" % (float(_task['org_time'])/3600.)
                if _task['spent_time'] is None:
                    _spent_time = "null"
                else:
                    _spent_time = "%0.2f" % (float(_task['spent_time'])/3600.)

                if week_end:
                    _text = (('text', ""),
                             ('text', ""),
                             ('text', u'%s' % _task['summary']),
                             ('text', ""),
                             ('text', u"%s" % _task['status']),
                             ('text', _org_time),
                             ('text', _spent_time),
                             ('text', u"%s" % _task['users'])
                             )
                    doc_appendix.addRow(_text)

    if week_end:
        doc_appendix.setTableFont(6)
        doc_appendix.addPageBreak()

    _print(u'项目共有 %d 个EPIC被分解到 %d 个功能点的 %d 个任务上。' %
           (_tot_epic, _tot_story, _tot_task), paragrap=_my_paragrap)

    _print(u'目前已完成 %d 个功能点（完成率%0.2f%%）和 %d 个任务（完成率%0.2f%%）。' %
           (_tot_done_story,
            float(_tot_done_story)*100./float(_tot_story),
            _tot_done_task,
            float(_tot_done_task)*100./float(_tot_task)), paragrap=_my_paragrap)

    if week_end:
        _print(u'项目明细情况参见附件【项目总体一览表】文件。' )

    """ 结束前的清理工作
    """
    db.close()
    doc.saveFile('%s-proj.docx' % project)
    if week_end:
        doc_appendix.saveFile('%s-proj-appendix.docx' % project)

    """删除过程文件"""
    _cmd = 'del /Q pic\\*'
    os.system(_cmd)

    _cmd = 'python doc2pdf.py %s-proj.docx %s-proj-%s.pdf' % \
           (project, project, time.strftime('%Y%m%d', time.localtime(time.time())))
    os.system(_cmd)
    if week_end:
        _cmd = 'python doc2pdf.py %s-proj-appendix.docx %s-proj-appendix-%s.pdf' % \
               (project, project, time.strftime('%Y%m%d', time.localtime(time.time())))
        os.system(_cmd)


if __name__ == '__main__':

    main(project_alias='HUBBLE')
