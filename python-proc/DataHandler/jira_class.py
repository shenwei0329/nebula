#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#   Jira处理类
#   ==========
#

from jira import JIRA
from jira.client import GreenHopper

import types
import json
import MySQLdb
from pymongo import MongoClient

import mysql_hdr


class jira_handler:

    def __init__(self, project_name):
        self.mongo_client = MongoClient()
        self.mongo_db = self.mongo_client.FAST
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
            _key = (u"%s" % _v).replace('.', '^')
            if not self.version.has_key(_key):
                self.version[_key] = {}
            self.version[_key][u"id"] = _v.id
            self.version[_key]['startDate'] = ""
            self.version[_key]['releaseDate'] = ""
            if 'startDate' in dir(_v):
                self.version[_key]['startDate'] = _v.startDate
            if 'releaseDate' in dir(_v):
                self.version[_key]['releaseDate'] = _v.releaseDate
            if self.mongo_db.project.find({"version": _key}).count() > 0:
                self.mongo_db.project.update({"version": _key},
                                             dict({"version": _key}, **self.version[_key]))
            else:
                _val = dict({"version": _key}, **self.version[_key])
                print _val
                self.mongo_db.project.insert(_val)
        self.issue = None

    def get_versions(self):
        _v = {}
        for _k in self.version:
            _key = (u"%s" % _k).replace('^', '.')
            _v[_key] = self.version[_k]
        return _v

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
                "org_time": self.issue.fields.timeoriginalestimate,
                "spent_time": self.issue.fields.timespent}

    def get_landmark(self):
        if len(self.issue.fields.fixVersions) > 0:
            return u"%s" % self.issue.fields.fixVersions[0]
        return ""

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

        if type(_time['agg_time']) is types.NoneType:
            _time['agg_time'] = ""
        if type(_time['org_time']) is types.NoneType:
            _time['org_time'] = ""
        if type(_time["spent_time"]) is types.NoneType:
            _time["spent_time"] = ""
        _issue = {u"%s" % self.show_name(): {
            "issue_type": self.get_type(),
            "users": self.get_users(),
            "status": self.get_status(),
            "landmark": self.get_landmark(),
            "point": self.get_story_point(),
            "agg_time": _time['agg_time'],
            "org_time": _time['org_time'],
            "spent_time": _time['spent_time']
        }}
        _key = u"%s" % self.show_name()
        if self.mongo_db.issue.find({"issue": _key}).count() > 0:
            self.mongo_db.issue.update({"issue": _key}, dict({"issue": _key}, **_issue[_key]))
        else:
            self.mongo_db.issue.insert(dict({"issue": _key}, **_issue[_key]))
        if self.mongo_db.issue_link.find({"issue": _key}).count() > 0:
            self.mongo_db.issue_link.update({"issue": _key},
                                            dict({"issue": _key}, **self.get_link()))
        else:
            self.mongo_db.issue_link.insert(dict({"issue": _key}, **self.get_link()))

        return _issue

    def get_users(self):
        """
        获取访问issue的用户
        :return:
        """
        watcher = self.jira.watchers(self.issue)
        _user = {}
        for watcher in watcher.watchers:
            _key = ('%s' % watcher.name)
            if watcher.active:
                if not _user.has_key(_key):
                    _user[_key] = {}
                _user[_key]['email'] = watcher.emailAddress
                # _user[_key]['name'] = watcher.displayName
        return _user

    def write_log(self, info):
        self.mongo_db.log.insert(info)

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


def into_db(sql_service, my_jira, kv):
    """
    同步Issue数据
    :param sql_service: 数据库处理器
    :param kv: Issue键值
    :return:
    """
    _key = kv.keys()[0]
    _sql = u'select issue_key,issue_value from jira_issue_t where issue_id="%s"' % _key
    _res = sql_service.do(_sql)
    _kv = {}
    if len(_res) > 0:
        for _r in _res:
            _kv[_r[0]] = _r[1]

        for _kk in kv[_key]:
            _value = (u"%s" % kv[_key][_kk])
            if _kk in _kv:
                if _kv[_kk] != _value:
                    """记录更改情况"""
                    _sql = u'update jira_issue_t set issue_value="%s",updated_at=now() ' \
                           u'where issue_id="%s" and issue_key="%s"' %\
                           (_value, _key, _kk, )
                    print _sql
                    sql_service.insert(_sql)
                    if _kk != "users":
                        _sql = u'insert into jira_log_t(' \
                               u'issue_id,rec_key,old_value,new_value,created_at,updated_at) ' \
                               u'values("%s","%s","%s","%s",now(),now())' %\
                               (_key, _kk, _kv[_kk], _value)
                        print _sql
                        sql_service.insert(_sql)
                    if _kk == "users":
                        print _kv[_kk]
                        _old = json.loads(_kv[_kk].replace("u'", '"').replace("'", '"'))
                        _log = {"issue_id": _key, "key": _kk, "old": _old, "new": kv[_key][_kk]}
                    else:
                        _log = {"issue_id": _key, "key": _kk, "old": _kv[_kk], "new": _value}
                    my_jira.write_log(_log)
            else:
                _sql = u'insert into jira_issue_t(issue_id,issue_key,issue_value,created_at,updated_at) ' \
                       u'values("%s","%s","%s",now(),now())' %\
                       (_key, _kk, _value)
                sql_service.insert(_sql)
    else:
        for _k in kv[_key]:
            _sql = u'insert into jira_issue_t(issue_id,issue_key,issue_value,created_at,updated_at) ' \
                   u'values("%s","%s","%s",now(),now())' % \
                   (_key, _k, kv[_key][_k])
            sql_service.insert(_sql)


def main():

    """连接数据库"""
    db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    my_sql = mysql_hdr.SqlService(db)

    my_jira = jira_handler('FAST')
    """
    _info = my_jira.get_pj_info()
    print(u"项目名称：%s，负责人：%s" % (_info['pj_name'], _info['pj_manager']))
    """

    """获取项目版本信息
    """
    versions = my_jira.get_versions()
    _versions = sorted(versions)
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
        _version[u"%s" % _v][u"startDate"] = versions[_v][u"startDate"]
        _version[u"%s" % _v][u"releaseDate"] = versions[_v][u"releaseDate"]
        _version[u"%s" % _v][u"issues"][u"key"] = kv
        _version[u"%s" % _v][u"issues"][u"link"] = kv_link

    """获取DB的里程碑信息
    """
    _sql = u'select name,start_date,release_date from jira_landmark_t where pj_id="FAST"'
    _res = my_sql.do(_sql)
    _db_rec = {}
    for _r in _res:
        _db_rec[_r[0]] = {'start_date': _r[1],
                          'release_date': _r[2]}

    for _v in sorted(_version, key=lambda a: a.split(u'（')[1]):
        print u"里程碑：%s" % _v, \
            u"\t startDate: %s" % versions[_v][u"startDate"],\
            u"\t releaseDate: %s" % versions[_v][u"releaseDate"]
        """同步里程碑信息
        """
        if _v in _db_rec:
            if versions[_v][u"startDate"] != _db_rec[_v]['start_date']:
                _sql = u'update jira_landmark_t set start_date="%s",updated_at=now() ' \
                       u'where pj_id="FAST" and name="%s"' % (_v, versions[_v][u"startDate"])
                print _sql
                my_sql.insert(_sql)
            if versions[_v][u"releaseDate"] != _db_rec[_v]['release_date']:
                _sql = u'update jira_landmark_t set release_date="%s",updated_at=now() ' \
                       u'where pj_id="FAST" and name="%s"' % (_v, versions[_v][u"releaseDate"])
                print _sql
                my_sql.insert(_sql)
        else:
            _sql = u'insert into jira_landmark_t(pj_id,name,start_date,release_date,created_at,updated_at) ' \
                   u'values("FAST","%s","%s","%s",now(),now())' % \
                   (_v, versions[_v][u"startDate"], versions[_v][u"releaseDate"])
            print _sql
            my_sql.insert(_sql)

        for _key in _version[_v][u"issues"][u"key"]:
            print(u"[类型：%s]: %d（个）" % (_key, _version[_v][u"issues"][u"key"][_key]))
            for __v in _version[_v][u"issues"][u"link"][_key]:
                print u'\t状态：%s' % __v
                for __story in _version[_v][u"issues"][u"link"][_key][__v]:
                    """里程碑里所有story
                    """
                    print u"\t\t- story：",
                    my_jira.set_issue_by_name(__story)
                    _kv = my_jira.show_issue()
                    into_db(my_sql, my_jira, _kv)
                    if task_link.has_key(__story):
                        for _task in task_link[__story]:
                            print u"\t\t\t 任务: ",
                            my_jira.set_issue_by_name(_task)
                            _kv = my_jira.show_issue()
                            into_db(my_sql, my_jira, _kv)
                            _link = my_jira.get_link()
                            for _l in _link:
                                for __l in _link[_l]:
                                    if __l == __story:
                                        continue
                                    print "\t\t\t\t",
                                    my_jira.set_issue_by_name(__l)
                                    _kv = my_jira.show_issue()
                                    into_db(my_sql, my_jira, _kv)


if __name__ == '__main__':
    main()
