#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#   Jira处理类
#   ==========
#

from jira import JIRA
from jira.client import GreenHopper

import types,json


class jira_handler:

    def __init__(self, project_name):
        self.jira = JIRA('http://172.16.60.13:8080', basic_auth=('shenwei','sw64419'))
        self.gh = GreenHopper({'server': 'http://172.16.60.13:8080'}, basic_auth=('shenwei', 'sw64419'))
        self.name = project_name
        self.project = self.jira.project(self.name)
        self.pj_name = u"%s" % self.project.name
        self.pj_manager = u"%s" % self.project.lead.displayName
        """获取项目版本信息
        """
        _versions = self.jira.project_versions(self.name)
        self.version = {}
        for _v in _versions:
            if not self.version.has_key(u"%s" % _v):
                self.version[u"%s" % _v] = {}
            self.version[u"%s" % _v][u"id"] = _v.id
            if 'startDate' in dir(_v):
                self.version[u"%s" % _v]['startDate'] = _v.startDate
            if 'releaseDate' in dir(_v):
                self.version[u"%s" % _v]['releaseDate'] = _v.releaseDate
        self.issue = None

    def get_versions(self):
        return self.version

    def get_pj_info(self):
        return {'pj_name': self.pj_name, 'pj_manager': self.pj_manager}

    def set_issue_by_name(self, issue_id):
        self.issue = self.jira.issue(issue_id)

    def print_green_hopper(self):
        _f = self.gh.fields()
        for __f in _f:
            __cns = __f['clauseNames']
            print('-' * 8)
            for _n in __cns:
                print u"name: %s" % _n
            print "id: ", u"%s" % __f['id']
            print "name: ", u"%s" % __f['name']

    def get_story_point(self):
        if type(self.issue.fields.customfield_10304) is not types.NoneType:
            return self.issue.fields.customfield_10304
        return -1.

    def get_task_time(self):
        return {"agg_time": self.issue.fields.aggregatetimeestimate,
                "org_time": self.issue.fields.timeoriginalestimate}

    def get_landmark(self):
        if len(self.issue.fields.fixVersions) > 0:
            return u"%s" % self.issue.fields.fixVersions[0]
        return None

    def get_desc(self):
        return u"%s" % self.issue.fields.summary

    def show_name(self):
        return u"%s" % str(self.issue)

    def get_type(self):
        return u"%s" % self.issue.fields.issuetype

    def get_status(self):
        return u"%s" % self.issue.fields.status

    def get_subtasks(self):
        """
        收集issue的相关子任务的issue
        :return: 相关issue字典
        """
        link = {}
        if not link.has_key(self.show_name()):
            link[self.show_name()] = []
        _task_issues = self.issue.fields.subtasks
        for _t in _task_issues:
            link[self.show_name()].append(u"%s" % _t)
        return link

    def get_link(self):
        """
        收集issue的相关issue
        :return: 相关issue字典
        """
        link = {}
        if not link.has_key(self.show_name()):
            link[self.show_name()] = []
        _task_issues = self.issue.fields.issuelinks
        for _t in _task_issues:
            if "outwardIssue" in dir(_t):
                """该story相关的任务"""
                link[self.show_name()].append(u"%s" % _t.outwardIssue)
            if "inwardIssue" in dir(_t):
                """该story相关的任务"""
                link[self.show_name()].append(u"%s" % _t.inwardIssue)
        return link

    def show_issue(self):
        """
        显示issue信息
        :return:
        """
        print("[%s]-%s" % (self.show_name(), self.get_desc())),
        print u"类型：%s" % self.get_type(),
        print(u'状态：%s' % self.get_status()),

        print u"里程碑：%s" % self.get_landmark(),
        print u"Story Points = %0.2f" % self.get_story_point(),
        _time = self.get_task_time()
        print u"估计工时：%s，剩余工时：%s" % (_time['agg_time'], _time['org_time'])

    def get_users(self):
        """
        获取访问issue的用户
        :return:
        """
        watcher = self.jira.watchers(self.issue)
        _user = {}
        for watcher in watcher.watchers:
            if watcher.active:
                if not _user.has_key(watcher.emailAddress):
                    _user[watcher.emailAddress] = {}
                _user[watcher.emailAddress]['alias'] = watcher.name
                _user[watcher.emailAddress]['name'] = watcher.displayName
        return _user

    def scan_issue(self, bg_date, keys, version):
        """
        扫描project收集相关版本的issue信息
        :param bg_date: 起始日期，如 2018-1-31
        :param keys: 关键字，[u'story', u'故事']
        :param version: 版本，里程碑
        :return: 按issue类型进行统计值kv_sum，issue链kv_link，相关任务链task_link
        """
        jql_sql = u'project=%s AND created >= %s ORDER BY created DESC' % (self.name, bg_date)
        total = 0
        kv_sum = {}
        kv_link = {}
        task_link = {}

        while True:
            issues = self.jira.search_issues(jql_sql, maxResults=100, startAt=total)
            for issue in issues:

                if (u"%s" % issue.fields.issuetype) not in keys:
                    continue

                self.issue = issue

                if self.get_landmark() == version:

                    """收集story相关的任务"""
                    task_link.update(self.get_link())

                    _type = self.get_type()
                    _status = self.get_status()
                    if not kv_sum.has_key(_type):
                        kv_sum[_type] = 0
                        kv_link[_type] = {}

                    kv_sum[_type] += 1
                    if not (kv_link[_type]).has_key(_status):
                        (kv_link[_type])[_status] = []
                    (kv_link[_type])[_status].append(self.show_name())

            if len(issues) == 100:
                total += 100
            else:
                break
        return kv_sum, kv_link, task_link


def main():

    my_jira = jira_handler('FAST')
    _info = my_jira.get_pj_info()
    print(u"项目名称：%s，负责人：%s" % (_info['pj_name'], _info['pj_manager']))

    """获取项目版本信息
    """
    _versions = sorted(my_jira.get_versions())
    task_link = {}
    _version = {}
    for _v in _versions:
        if u"3.0 " not in u"%s" % _v:
            continue
        if not _version.has_key(u"%s" % _v):
            _version[u"%s" % _v] = {}
        kv, kv_link, _task_link = my_jira.scan_issue('2018-1-1', [u'story'], version=u"%s" % _v)
        task_link.update(_task_link)
        if not _version[u"%s" % _v].has_key(u"issues"):
            _version[u"%s" % _v][u"issues"] = {}
        _version[u"%s" % _v][u"issues"][u"key"] = kv
        _version[u"%s" % _v][u"issues"][u"link"] = kv_link

    for _v in _version:
        print u"里程碑：%s" % _v
        for _key in _version[_v][u"issues"][u"key"]:
            print(u"[类型：%s]: %d（个）" % (_key, _version[_v][u"issues"][u"key"][_key]))
            for __v in _version[_v][u"issues"][u"link"][_key]:
                print u'\t状态：%s' % __v
                for __story in _version[_v][u"issues"][u"link"][_key][__v]:
                    print u"\t\t- story：",
                    my_jira.set_issue_by_name(__story)
                    my_jira.show_issue()
                    if task_link.has_key(__story):
                        for _task in task_link[__story]:
                            print u"\t\t\t 任务: ",
                            my_jira.set_issue_by_name(_task)
                            my_jira.show_issue()
                            _link = my_jira.get_link()
                            for _l in _link:
                                for __l in _link[_l]:
                                    print "\t\t\t\t",
                                    my_jira.set_issue_by_name(__l)
                                    my_jira.show_issue()


if __name__ == '__main__':
    main()
