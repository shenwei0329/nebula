#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#   Jira处理类
#   ==========
#
#   2018.3.6@chengdu
#   ----------------
#   1）针对产品研发过程以epic关联story；
#   2）以story关联task。
#   对程序进行“规范化”处理
#

import sys
from jira import JIRA
from jira.client import GreenHopper

import types
import time
import json
import MySQLdb
from pymongo import MongoClient
import mongodb_class

import mysql_hdr


class jira_handler:
    """
    Jira处理类。
    【备注】：目前存在Jira方法与Issue对象混合在一起的不足。
    【改进】：将Jira方法与Issue对象实体分离，各自进行类定义。
    """

    def __init__(self, project_name):
        self.mongo_db = mongodb_class.mongoDB(project_name)
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
        self.sprints = self._get_sprints()
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
            self.mongo_db.handler("project", "update",
                                  {"version": _key}, dict({"version": _key}, **self.version[_key]))
        self.issue = None

    def _get_board(self):
        _boards = self.jira.boards()
        for _b in _boards:
            if self.name in _b.name:
                return _b.id
        return None

    def transDate(self, str):
        print("---> transDate [%s] <---" % str)
        if str != None and str != u'无':
            _s = str.\
                replace(u'十一月', '11').\
                replace(u'十二月', '12').\
                replace(u'一月', '1').\
                replace(u'二月', '2').\
                replace(u'三月', '3').\
                replace(u'四月', '4').\
                replace(u'五月', '5').\
                replace(u'六月', '6').\
                replace(u'七月', '7').\
                replace(u'八月', '8').\
                replace(u'九月', '9').\
                replace(u'十月', '10')
            _time = time.strptime(_s, '%d/%m/%y')
            return time.strftime('%Y-%m-%d', _time)
        else:
            return ""

    def _get_sprints(self):
        """
        获取看板内sprint列表
        :return: sprint列表 [ name, startDate, endDate, state ]
        """
        _list = []
        _b_id = self._get_board()
        if type(_b_id) is not types.NoneType:
            _sprints = self.jira.sprints(_b_id)
            for _s in _sprints:
                _sprint = self.jira.sprint(_s.id)
                _data = {'name': _s.name,
                         'startDate': self.transDate(_sprint.startDate.split(' ')[0]),
                         'endDate': self.transDate(_sprint.endDate.split(' ')[0]),
                         'state': _s.state
                         }
                _list.append(_data)
            return _list
        return None

    def get_sprints(self):
        return self.sprints

    def get_current_sprint(self):
        """
        获取本阶段sprint名称
        :return: 返回状态为ACTIVE的sprint的名称
        """
        if type(self.sprints) is not types.NoneType:
            for _s in self.sprints:
                if _s['state'] == 'ACTIVE':
                    return (_s['name'], _s['startDate'], _s['endDate']), _next
                _next = (_s['name'], _s['startDate'], _s['endDate'])
        return None

    def get_sprint(self):
        """
        获取当前Issue的sprint定义
        :return: sprint定义
        """
        if "customfield_10501" in self.issue.raw['fields'] and \
                type(self.issue.fields.customfield_10501) is not types.NoneType:
            return u'%s' % (",".join(item.split('name=')[1].split(',')[0]
                                      for item in self.issue.fields.customfield_10501))
            # return u'%s' % self.issue.fields.customfield_10501[0].split('name=')[1].split(',')[0]
        return None

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
        """
        获取Issue(story)的预置成本, 1 point = 4 hours
        :return: 预置成本
        """
        if "customfield_10304" in self.issue.raw['fields'] and \
                type(self.issue.fields.customfield_10304) is not types.NoneType:
            return self.issue.fields.customfield_10304
        return None

    def get_task_time(self):
        return {"agg_time": self.issue.fields.aggregatetimeestimate,
                "org_time": self.issue.fields.timeoriginalestimate,
                "spent_time": self.issue.fields.timespent}

    def get_landmark(self):
        if len(self.issue.fields.fixVersions) > 0:
            return u"%s" % self.issue.fields.fixVersions[0]
        if len(self.issue.fields.versions) > 0:
            # print self.show_name(), " version: %s" % self.issue.fields.versions[0]
            return u"%s" % self.issue.fields.versions[0]
        return ""

    def get_desc(self):
        return self.issue.fields.summary

    def show_name(self):
        return str(self.issue)

    def get_type(self):
        return u"%s" % self.issue.fields.issuetype

    def get_status(self):
        """
        获取Issue的状态，待办、处理中、待测试、测试中、完成
        :return:
        """
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

    def get_child_requirement(self):

        link = []
        jql = "issue in  childrenOfParentRequirement('%s')" % self.show_name()
        # print jql
        tot = 0
        while True:
            issues = self.jira.search_issues(jql, maxResults=100, startAt=tot)
            for issue in issues:
                link.append(issue.key)
            if len(issues) == 100:
                tot += 100
            else:
                break
        return link

    def get_epic_link(self, jql):

        print(">>> get_epic_link<%s>" % jql)
        total = 0
        _issue_name = self.show_name()
        task_link = {_issue_name: []}
        while True:
            issues = self.jira.search_issues(jql, maxResults=100, startAt=total)
            for issue in issues:
                self.issue = issue
                self.sync_issue()
                """收集epic相关的story和任务"""
                task_link[_issue_name].append(self.show_name())
            if len(issues) == 100:
                total += 100
            else:
                break
        print task_link
        self.set_issue_by_name(_issue_name)
        return task_link

    def get_link(self):
        """
        收集issue的相关issue
        :return: 相关issue字典
        """
        link = {self.show_name(): []}

        """兼容以前: 与story相关的task是通过issulelinks关联的"""
        _task_issues = self.issue.fields.issuelinks
        for _t in _task_issues:
            if "outwardIssue" in dir(_t):
                """该story相关的任务"""
                link[self.show_name()].append(u"%s" % _t.outwardIssue)
            if "inwardIssue" in dir(_t):
                """该story相关的任务"""
                link[self.show_name()].append(u"%s" % _t.inwardIssue)

        """采用synapseRT插件后对需求的管理"""
        _task_issues = self.get_child_requirement()
        for _t in _task_issues:
            link[self.show_name()].append(_t)

        return link

    def sync_issue(self):
        """
        同步issue数据，同时完成重要参量的变更日志。
        :return:
        """
        _components = u"%s" % (', '.join(comp.name for comp in self.issue.fields.components))
        _key = u"%s" % self.show_name()
        _time = self.get_task_time()
        _epic_link = None
        if "customfield_11300" in self.issue.raw['fields'] and \
                type(self.issue.fields.customfield_11300) is not types.NoneType:
            _epic_link = self.issue.raw['fields']["customfield_11300"]
        _issue = {u"%s" % self.show_name(): {
                "issue_type": self.get_type(),
                "created": self.issue.fields.created,
                "updated": self.issue.fields.updated,
                "lastViewed": self.issue.fields.lastViewed,
                "users": self.get_users(),
                "status": self.get_status(),
                "landmark": self.get_landmark(),
                "point": self.get_story_point(),
                "agg_time": _time['agg_time'],
                "org_time": _time['org_time'],
                "summary": self.issue.fields.summary,
                "spent_time": _time['spent_time'],
                "sprint": self.get_sprint(),
                "epic_link": _epic_link,
                "components": _components
            }}
        _old_issue = self.mongo_db.handler("issue", "find_one", {"issue": _key})
        if _old_issue is None:
            self.mongo_db.handler("issue", "update",
                                  {"issue": _key}, dict({"issue": _key}, **_issue[_key]))
        else:
            _change = False
            for _item in ['issue_type','created','updated','users','status',
                          'landmark','point','agg_time','org_time',
                          'summary','spent_time','sprint','epic_link']:
                if _old_issue[_item] != _issue[_key][_item]:
                    _log = {"issue_id": _key, "key": _item,
                            "old": _old_issue[_item], "new": _issue[_key][_item]}
                    self.write_log(_log)
                    _change = True
            _change = True
            if _change:
                self.mongo_db.handler("issue", "update",
                                      {"issue": _key}, dict({"issue": _key}, **_issue[_key]))

    def get_issue_link(self):
        _link = self.get_link()
        print "---> get_issue_link: ", _link
        return _link

    def sync_issue_link(self):
        _key = u"%s" % self.show_name()
        _link = self.get_link()

        print "sync_issue_link: ", _link

        self.mongo_db.handler("issue_link", "update",
                              {"issue": _key}, dict({"issue": _key}, **_link))
        return _link

    def show_issue(self):
        """
        显示issue信息
        :return:
        """
        print(u"[%s]" % self.show_name()),
        print u"类型：%s" % self.get_type(),
        print(u'状态：%s' % self.get_status()),
        print u"里程碑：%s" % self.get_landmark()

    def get_users(self):
        """
        获取访问issue的用户
        2018.3.1：改为 经办人 assignee
        :return:
        watcher = self.jira.watchers(self.issue)
        _user = u"%s" % (', '.join(watcher.displayName for watcher in watcher.watchers))
        """
        if type(self.issue.raw['fields']["assignee"]) is types.NoneType:
            return None
        return (u"%s" % self.issue.raw['fields']["assignee"]['displayName']).replace(' ', '')

    def write_log(self, info):
        print "---<write_log>---: ",info
        self.mongo_db.handler("log", "insert", info)

    def write_worklog(self, info):
        """
        写入或更新 工作日志记录。
        :param info: 新的日志数据
        :return:
        """
        _search = {'issue': info['issue'],
                   'id': info['id']}
        self.mongo_db.handler('worklog', 'update', _search, info)

    def clear_worklog(self, worklog_id):
        """
        清除"不存在"的记录!
        :param worklog_id: 存在的worklog_id
        :return:
        """
        _set = {'timeSpentSeconds': 0}
        if len(worklog_id) > 0:
            _search = {"issue": self.show_name(), "id": {"$not": {"$in": worklog_id}}}
        else:
            _search = {"issue": self.show_name()}
        # self.mongo_db.handler('worklog', 'remove', _search)
        """保留原记录，将其用时值设置为0，以便事后跟踪"""
        self.mongo_db.handler('worklog', 'update', _search, _set)

    def sync_worklog(self):
        """
        获取指定 issue 的工作日志记录。
        - 2018.4.2：针对以前有的，但现在没有的 日志记录 的处理？！清除其spent时间
        :return:
        """
        worklogs = self.jira.worklogs(self.show_name())
        wl = {}
        _id = []
        for worklog in worklogs:
            wl['issue'] = self.show_name()
            wl['author'] = u'%s' % worklog.author
            wl['comment'] = u'%s' % worklog.comment
            wl['timeSpent'] = worklog.timeSpent
            wl['timeSpentSeconds'] = worklog.timeSpentSeconds
            wl['updated'] = worklog.updated
            wl['created'] = worklog.created
            wl['started'] = worklog.started
            wl['id'] = worklog.id
            _id.append(worklog.id)
            self.write_worklog(wl)
        """同时同步Issue的变动日志"""
        """ 因worklog可随意更改或删除, 有必要实时清除多余的记录!"""
        self.clear_worklog(_id)

        self.sync_changelog()

    def scan_task_by_sprint(self, sprint):
        """
        通过sprint获取Issue，以便获取它们的 工作日志
        :param sprint: 当前的sprint名称
        :return: Issue列表
        """
        jql_sql = u'project=%s AND Sprint = "%s" ORDER BY created DESC' %\
                  (self.name, sprint)
        total = 0
        tasks = []
        while True:
            issues = self.jira.search_issues(jql_sql, maxResults=100, startAt=total)
            for issue in issues:
                self.issue = issue
                """同步issue"""
                self.sync_issue()
                self.sync_worklog()
                self.sync_issue_link()
                tasks.append(self.show_name())
            if len(issues) == 100:
                total += 100
            else:
                break
        return tasks

    def scan_epic(self, bg_date):
        """
        扫描project收集epic信息
        :param bg_date: 起始日期，如 2018-1-31
        :param issue_type：指定issue类型
        :return: 按issue类型进行统计值kv_sum，issue链kv_link，相关任务链task_link
        """
        jql_sql = u'project=%s AND issuetype=epic AND created >= %s ORDER BY created DESC' % (
            self.name, bg_date)
        total = 0
        story_link = []

        while True:
            issues = self.jira.search_issues(jql_sql, maxResults=100, startAt=total)
            for issue in issues:
                self.issue = issue
                """同步issue"""
                # self.show_issue()
                self.sync_issue()
                """收集epic相关的story和任务"""
                _jql = u'project=%s AND "Epic Link"=%s AND created >= %s ORDER BY created DESC' % \
                       (self.name, self.show_name(), bg_date)
                _link = self.get_epic_link(_jql)
                """同步epic的link"""
                # print "--> epic link: ", dict({"issue": self.show_name()}, **_link)
                self.mongo_db.handler("issue_link", "update",
                                      {"issue": self.show_name()},
                                      dict({"issue": self.show_name()}, **_link))
                story_link += _link[self.show_name()]

            if len(issues) == 100:
                total += 100
            else:
                break
        return story_link

    def scan_story(self, bg_date):
        """
        按 project 获取其下所有 story 数据。
        :param bg_date: 开始搜索的日期
        :return:
        """
        jql_sql = u'project=%s AND issuetype=story AND created >= %s ORDER BY created DESC' % (
            self.name, bg_date)
        total = 0
        task_link = []

        while True:
            issues = self.jira.search_issues(jql_sql, maxResults=100, startAt=total)
            for issue in issues:
                self.issue = issue
                """同步issue"""
                # self.show_issue()
                self.sync_issue()
                """收集story相关的任务"""
                _link = self.sync_issue_link()
                """同步epic的link"""
                self.mongo_db.handler("issue_link", "update",
                                      {"issue": self.show_name()},
                                      dict({"issue": self.show_name()}, **_link))
                task_link += _link[self.show_name()]

            if len(issues) == 100:
                total += 100
            else:
                break
        return task_link

    def scan_task(self, bg_date):
        """
        按 project 获取其下所有与执行相关的 issue 数据。
        :param bg_date: 开始搜索的日期
        :return:
        """
        jql_sql = u'project=%s AND ( issuetype=task OR' \
                  u' issuetype=任务 OR' \
                  u' issuetype=故障 OR' \
                  u' issuetype=Bug OR' \
                  u' issuetype=Sub-task OR' \
                  u' issuetype=子任务 ) AND' \
                  u' created >= %s ORDER BY created DESC' % (self.name, bg_date)
        print jql_sql
        total = 0
        task_link = []

        while True:
            issues = self.jira.search_issues(jql_sql, maxResults=100, startAt=total)
            for issue in issues:
                self.issue = issue
                """同步issue"""
                self.show_issue()
                self.sync_issue()
                # self.sync_changelog()
                self.sync_worklog()
                task_link.append(self.show_name())
            if len(issues) == 100:
                total += 100
            else:
                break
        return task_link

    def sync_changelog(self):
        """
        获取指定 issue 的 变更日志记录
        :return:
        """
        issue = self.jira.issue(self.show_name(), expand='changelog')
        changelog = issue.changelog
        for history in changelog.histories:
            for item in history.items:
                _data = {'issue': self.show_name(),
                         'field': item.field,
                         'author': u"%s" % history.author,
                         'date': history.created,
                         'old': getattr(item, 'fromString'),
                         'new': getattr(item, 'toString')
                         }
                if self.mongo_db.handler('changelog', 'find_one', _data) is None:
                    self.mongo_db.handler('changelog', 'insert', _data)


def into_db(sql_service, my_jira, kv):
    """
    同步Issue数据
    :param sql_service: 数据库处理器
    :param my_jira: mongoDB库
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
                    """
                    if _kk == "users":
                        print _kv[_kk]
                        # _old = json.loads(_kv[_kk].replace("u'", '"').replace("'", '"'))
                        _old = _kv[_kk]
                        _log = {"issue_id": _key, "key": _kk, "old": _old, "new": kv[_key][_kk]}
                    else:
                        _log = {"issue_id": _key, "key": _kk, "old": _kv[_kk], "new": _value}
                    """
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


def do_with_epic(myjira, sprints):

    issue_link = myjira.scan_epic('2017-12-1')

    for issue in issue_link:

        myjira.set_issue_by_name(issue)
        myjira.sync_issue()
        myjira.show_issue()

        if myjira.get_type().lower() in [u'任务', 'task']:
            myjira.sync_worklog()

        if myjira.get_type() in [u'story', u'improvement', u'New Feature', u'改进', u'新功能', u'故障']:
            _my_name = myjira.show_name()
            """获取story等下属的task"""
            _link = myjira.sync_issue_link()
            for _issue in _link[_my_name]:
                __my_name = _issue
                myjira.set_issue_by_name(__my_name)
                myjira.sync_issue()
                myjira.show_issue()
                """获取task下属的subtask？"""
                _task_link = myjira.sync_issue_link()
                for _task in _task_link[__my_name]:
                    myjira.set_issue_by_name(_task)
                    myjira.sync_issue()
                    myjira.sync_worklog()
                    myjira.show_issue()

    """基于sprint收集Issue信息"""
    if type(sprints) != types.NoneType:
        for _sprint in sprints:
            tasks = myjira.scan_task_by_sprint(_sprint['name'])
            for _task in tasks:
                myjira.set_issue_by_name(_task)
                myjira.sync_issue()
                myjira.sync_worklog()
                myjira.show_issue()


def do_with_story(myjira, sprints):

    issue_link = myjira.scan_story('2017-12-1')
    for issue in issue_link:
        myjira.set_issue_by_name(issue)
        myjira.sync_issue()
        myjira.show_issue()
        myjira.sync_worklog()
    myjira.scan_task('2017-12-1')


def do_with_task(myjira):

    myjira.scan_task('2017-12-1')


def main(project_alias=None, issue_type=None):

    """连接数据库"""
    # db = MySQLdb.connect(host="47.93.192.232",user="root",passwd="sw64419",db="nebula",charset='utf8')
    # my_sql = mysql_hdr.SqlService(db)

    my_jira = jira_handler(project_alias)
    _sprints = my_jira.get_sprints()

    if issue_type == 'epic':
        do_with_epic(my_jira, _sprints)
    elif issue_type == 'story':
        do_with_story(my_jira, _sprints)
    elif issue_type == 'task':
        do_with_task(my_jira)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], issue_type=sys.argv[2])
    else:
        print(u"\tUsage: %s project_alias issue_type" % sys.argv[0])
