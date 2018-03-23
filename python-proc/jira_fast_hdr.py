#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# 针对 FAST 3.0 在JIRA上的任务项数据进行采集、入库
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
    从 JIRA 导入 FAST 全部Issue数据（2018-1-31执行）
    :param cur: 数据库
    :param jira: Jira
    :return:
    """

    _insert_n = 0
    _update_n = 0
    _non_op_n = 0

    issue_id = []
    Task = {}
    total = 0
    while True:
        issues = jira.search_issues('project=%s ORDER BY created DESC' %
                                    project_alias, maxResults=100, startAt=total)
        for issue in issues:

            issue_id.append(str(issue))

            watcher = jira.watchers(issue)
            # print("Issue has {} watcher(s)".format(watcher.watchCount))
            _user = {'alias': '', 'name': '', 'email': ''}
            for watcher in watcher.watchers:
                if watcher.active:
                    _user['alias'] += u"<%s>" % watcher.name
                    _user['name'] += u"<%s>" % watcher.displayName
                    _user['email'] += u"<%s>" % watcher.emailAddress

            if type(issue.fields.description) is types.NoneType:
                Task[issue.key] = [issue.key,
                                   issue.fields.summary.replace('"', '^').replace("'", '^'),
                                   "",
                                   _user,
                                   u'%s' % issue.fields.status,
                                   issue.fields.created,
                                   issue.fields.updated,
                                   issue.fields.issuetype]
            else:
                _desc = issue.fields.description.replace('\n', '').replace('\r', '').replace('"', '^').replace("'", '^')
                Task[issue.key] = [ issue.key,
                                    issue.fields.summary.replace('"', '^').replace("'", '^'),
                                    _desc,
                                    _user,
                                    u'%s' % issue.fields.status,
                                    issue.fields.created,
                                    issue.fields.updated,
                                    issue.fields.issuetype]

        total += len(issues)
        if total % 100 != 0:
            break

    _keys = sorted(Task.keys(), reverse=True)
    for _v in _keys:
        _sql = 'select count(*) from jira_task_t where issue_id="%s" and project_alias="%s"' % \
               (Task[_v][0],project_alias)
        _n = doSQLcount(cur, _sql)
        if _n>0:
            """记录已存在：判断记录的“summary、state、completeDate”是否变化
            """
            _sql = 'select issue_status,startDate,endDate,summary,users from jira_task_t where issue_id="%s"' %\
                   Task[_v][0]
            _res = doSQL(cur, _sql)
            for _r in _res:
                _sql = None
                if str(_r[0]) != str(Task[_v][4]):
                    _sql = u'update jira_task_t set issue_status="%s"' % Task[_v][4]
                if str(_r[1]) != str(Task[_v][5]):
                    if _sql is None:
                        _sql = 'update jira_task_t set startDate="%s"' % str(Task[_v][5])
                    else:
                        _sql += ',startDate="%s"' % str(Task[_v][5])
                if str(_r[2]) != str(Task[_v][6]):
                    if _sql is None:
                        _sql = 'update jira_task_t set endDate="%s"' % str(Task[_v][6])
                    else:
                        _sql += ',endDate="%s"' % str(Task[_v][6])
                if str(_r[3]) != str(Task[_v][1]):
                    if _sql is None:
                        _sql = 'update jira_task_t set summary="%s"' % str(Task[_v][1])
                    else:
                        _sql += ',summary="%s"' % str(Task[_v][1])
                if str(_r[4]) != str(Task[_v][3]['name']):
                    if _sql is None:
                        _sql = 'update jira_task_t set users="%s",users_alias="%s",user_emails="%s"' %\
                               (str(Task[_v][3]['name']),str(Task[_v][3]['alias']),str(Task[_v][3]['email']))
                    else:
                        _sql += ',users="%s",users_alias="%s",user_emails="%s"' %\
                                (str(Task[_v][3]['name']),str(Task[_v][3]['alias']),str(Task[_v][3]['email']))

                if _sql is None:
                    # print("[%s]: No change!<%s,%s>" % (Task[_v][0],_r[0],_r[1]))
                    _non_op_n += 1
                    continue
                _sql += ' where issue_id="%s" and project_alias="%s"' % (Task[_v][0],project_alias)
                print _sql
                doSQL(cur, _sql)
                _update_n += 1
        else:
            """添加新记录
            """
            _sql = 'insert into jira_task_t(project_alias,issue_id,summary,description,' \
                   'users,users_alias,user_emails,startDate,endDate,issue_status,issue_type) ' \
                   'values("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")' % (
                    project_alias,
                    Task[_v][0],
                    Task[_v][1],
                    Task[_v][2],
                    Task[_v][3]['name'].replace(' ', ''),
                    Task[_v][3]['alias'].replace(' ', ''),
                    Task[_v][3]['email'],
                    Task[_v][5],
                    Task[_v][6],
                    Task[_v][4],
                    Task[_v][7])
            print _sql
            doSQLinsert(db, cur, _sql)
            _insert_n += 1

    return Task, [_update_n, _insert_n, _non_op_n], issue_id


if __name__ == '__main__':

    """连接JIRA系统"""
    jira = JIRA('http://172.16.60.13:8080',basic_auth=('shenwei', 'sw64419'))

    """连接数据库"""
    db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    # db = MySQLdb.connect(host="172.16.101.117",user="root",passwd="123456",db="nebula",charset='utf8')
    cur = db.cursor()

    _issue_id = []
    _sql = 'select issue_id from jira_task_t'
    _res = doSQL(cur, _sql)
    for _i in _res:
        _issue_id.append(str(_i[0]))

    Task,Quta,Issue_id = inputFASTtask(db, cur, jira, project_alias='FAST')
    """针对UPDATE的数据需要COMMIT"""
    db.commit()

    print(" number of be updated: %d" % Quta[0])
    print(" number of be inserted: %d" % Quta[1])
    print(" number of non-modified: %d" % Quta[2])
    print(".done")
