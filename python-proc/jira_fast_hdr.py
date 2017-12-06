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

def inputFASTtask(cur, jira):
    """
    从 JIRA 导入 FAST 任务数据
    :param cur: 数据库
    :param jira: Jira
    :return:
    """
    Task = {}
    issues = jira.search_issues('project = FAST ORDER BY created DESC', maxResults=10000)
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

            Task[issue] = [issue.fields.summary, issue.fields.description.replace('\n', '').replace('\r', ''),
                           _v,
                           _user]
    return Task

if __name__ == '__main__':

    """连接JIRA系统"""
    jira = JIRA('http://172.16.60.13:8080',basic_auth=('shenwei', 'sw64419'))

    """连接数据库"""
    db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    cur = db.cursor()

    Task = inputFASTtask(cur, jira)

    _keys = sorted(Task.keys(),reverse=True)
    for _v in _keys:
        print("\t%s, %s" % (Task[_v][0],Task[_v][1]))
        for _k in sorted(Task[_v][2].keys(),reverse=True):
            print("\t%s = %s" % (_k,Task[_v][2][_k]))
        print("\tUser: %s, Alias: %s, eMail: %s" % (Task[_v][3]['name'],Task[_v][3]['alias'],Task[_v][3]['email']))
        print("=" * 8)