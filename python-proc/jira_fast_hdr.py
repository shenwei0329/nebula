#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# 针对 FAST 1.0 在JIRA上的任务项数据进行采集、入库
# ================================================
#

from jira import JIRA
import types,json,sys,MySQLdb

reload(sys)
sys.setdefaultencoding('utf-8')

def doSQLinsert(db,cur,_sql):
    try:
        cur.execute(_sql)
        db.commit()
    except:
        db.rollback()

def doSQLcount(cur,_sql):
    try:
        cur.execute(_sql)
        _result = cur.fetchone()
        _n = _result[0]
        if _n is None:
            _n = 0
    except:
        _n = 0
    return _n

def doSQL(cur,_sql):
    cur.execute(_sql)
    return cur.fetchall()

def inputFASTtask(db, cur, jira, project_alias='FAST'):
    """
    从 JIRA 导入 FAST 任务数据
    :param cur: 数据库
    :param jira: Jira
    :return:
    """

    _insert_n = 0
    _update_n = 0
    _non_op_n = 0

    Task = {}
    issues = jira.search_issues('project = %s ORDER BY created DESC' % project_alias, maxResults=10000)
    for issue in issues:
        watcher = jira.watchers(issue)
        # print("Issue has {} watcher(s)".format(watcher.watchCount))
        _user = {}
        for watcher in watcher.watchers:
            if watcher.active:
                _user['alias'] = watcher.name
                _user['name'] = watcher.displayName
                _user['email'] = watcher.emailAddress

        if issue.fields.customfield_10501 is not None and len(issue.fields.customfield_10501) > 0:
            _s = issue.fields.customfield_10501[0][issue.fields.customfield_10501[0].index('['):]
            _s = _s.replace('[', '{"').replace(']', '"}').replace('=', '":"').replace(',', '","')
            _v = json.loads(_s)

            Task[issue] = [issue.id,
                           issue.fields.summary,
                           issue.fields.description.replace('\n', '').replace('\r', ''),
                           _v,
                           _user]

    _keys = sorted(Task.keys(), reverse=True)
    for _v in _keys:
        _sql = 'select count(*) from jira_task_t where issue_id=%s and project_alias="%s"' % \
               (Task[_v][0],project_alias)
        _n = doSQLcount(cur, _sql)
        if _n>0:
            """记录已存在：判断记录的“state、completeDate”是否变化
            """
            _sql = 'select state,completeDate from jira_task_t where issue_id=%s' % Task[_v][0]
            _res = doSQL(cur, _sql)
            for _r in _res:
                _sql = None
                if _r[0]!=Task[_v][3]['state']:
                    _sql = 'update jira_task_t set state="%s"' % Task[_v][3]['state']
                if _r[1]!=Task[_v][3]['completeDate']:
                    if _sql is None:
                        _sql = 'update jira_task_t set completeDate="%s"' % Task[_v][3]['completeDate']
                    else:
                        _sql += ',completeDate="%s"' % Task[_v][3]['completeDate']
                if _sql is None:
                    # print("[%s]: No change!<%s,%s>" % (Task[_v][0],_r[0],_r[1]))
                    _non_op_n += 1
                    continue
                _sql += ' where issue_id=%s and project_alias="%s"' % (Task[_v][0],project_alias)
                print _sql
                doSQL(cur, _sql)
                _update_n += 1
        else:
            """添加新记录
            """
            _sql = 'insert into jira_task_t(project_alias,issue_id,summary,description,state,sequence,' \
                   'stage_name,users,users_alias,user_emails,startDate,endDate,completeDate) ' \
                   'values("%s",%s,"%s","%s","%s",%s,"%s","%s","%s","%s","%s","%s","%s")' % (
                    project_alias,
                    Task[_v][0],
                    Task[_v][1],
                    Task[_v][2],
                    Task[_v][3]['state'],
                    Task[_v][3]['sequence'],
                    Task[_v][3]['name'],
                    Task[_v][4]['name'],
                    Task[_v][4]['alias'],
                    Task[_v][4]['email'],
                    Task[_v][3]['startDate'],
                    Task[_v][3]['endDate'],
                    Task[_v][3]['completeDate'])
            print _sql
            doSQLinsert(db, cur, _sql)
            _insert_n += 1

    return Task, [_update_n, _insert_n, _non_op_n]

if __name__ == '__main__':

    """连接JIRA系统"""
    jira = JIRA('http://172.16.60.13:8080',basic_auth=('shenwei', 'sw64419'))

    """连接数据库"""
    db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    cur = db.cursor()

    Task,Quta = inputFASTtask(db, cur, jira, project_alias='FAST')
    """针对UPDATE的数据需要COMMIT"""
    db.commit()

    """
    _keys = sorted(Task.keys(),reverse=True)
    for _v in _keys:
        print("\t%s, %s" % (Task[_v][1],Task[_v][2]))
        for _k in sorted(Task[_v][3].keys(),reverse=True):
            print("\t%s = %s" % (_k,Task[_v][3][_k]))
        print("\tUser: %s, Alias: %s, eMail: %s" % (Task[_v][4]['name'],Task[_v][4]['alias'],Task[_v][4]['email']))
        print("=" * 8)
    """
    print(" number of be updated: %d" % Quta[0])
    print(" number of be inserted: %d" % Quta[1])
    print(" number of non-modified: %d" % Quta[2])
    print(".done")
