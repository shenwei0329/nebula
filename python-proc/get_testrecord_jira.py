#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# 导入“测试记录数据”
# ====================
# Created：2017.12.15 by shenwei @ ChengDu
#
#

import MySQLdb, sys, datetime
from jira import JIRA

reload(sys)
sys.setdefaultencoding('utf-8')

ReplaceTable = {
    u"whitehole v1.0r1m1": "WhiteHole^1.0r1m1",
    u"测试-Apollo": "Apollo^1.0",
    u"hubble1.8": "Hubble^1.8",
    u"FAST云平台测试": "FAST^3.0"
}

def doSQLinsert(db, sql, cur):
    """
    添加记录
    :param db: 数据库
    :param cur: 当前光标
    :param sql: SQL语句（INSERT）
    :return:
    """

    try:
        cur.execute(sql)
        db.commit()
    except:
        print(">>>Err(mysql): %s" % sql)
        db.rollback()

def getIssue(jira, bg_date, ed_date):
    """
    导入“测试记录数据”：
    err_summary,err_key,err_id,err_type,err_state,err_pj_key,err_pj_name,err_level,err_result,err_opr,
    err_rpr=#,err_cr_date,err_md_date,err_ed_date,err_version_ing,err_mod_1,err_desc,err_version_ed=#,err_mod_2=#
    【注意】该过程与时间窗口相关，应在每周一上班时收集上一周“周一至周日”的数据。
    :param jira: JIRA系统入口
    :param bg_date: 起始日期
    :param ed_date: 截止日期
    :return:
    """
    """ 目前项目：HBLE, WHIT, FASTT, AP；问题类型：Improvement, Bug, 缺陷 """
    issues = jira.search_issues('project in (HBLE, WHIT, FASTT, AP) AND '
                                'issuetype in (Improvement, Bug, 缺陷) AND updated >= %s AND updated <= %s' %
                                (bg_date,ed_date), maxResults=10000)
    _SQLcmd = []
    for issue in issues:
        watcher = jira.watchers(issue)
        _user = {}
        for watcher in watcher.watchers:
            if watcher.active:
                _user['alias'] = watcher.name
                _user['name'] = watcher.displayName
                _user['email'] = watcher.emailAddress

        if len(issue.fields.versions)>0:
            _versions = issue.fields.versions[0].name
        else:
            _versions = '#'
        if len(issue.fields.components)>0:
            _components = issue.fields.components[0].name
        else:
            _components = '#'

        if not ReplaceTable.has_key(issue.fields.project.name):
            print u"%s" % issue.fields.project.name
            ReplaceTable[issue.fields.project.name] = '#'

        if issue.fields.resolution is None:
            _resolution = '#'
        else:
            _resolution = issue.fields.resolution

        _str = u'insert into testrecord_t(' \
               u'err_summary,err_key,err_id,err_type,err_state,err_pj_key,err_pj_name,' \
               u'err_level,err_result,err_opr,err_rpr,err_cr_date,err_md_date,err_ed_date,' \
               u'err_version_ing,err_mod_1,err_desc,err_version_ed,err_mod_2,created_at,updated_at) ' \
               u'values("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","#","%s","%s","%s",' \
               u'"%s","%s","%s","#","#",now(),now())' % \
               (issue.fields.summary.replace('\r', '').replace('\n', ',').replace(' ', '').replace('"', "'"),
                issue.key,
                issue.id,
                issue.fields.issuetype,
                issue.fields.status,
                issue.fields.project.key,
                ReplaceTable[issue.fields.project.name],
                issue.fields.priority,
                _resolution,
                _user['name'],
                issue.fields.created,
                issue.fields.updated,
                issue.fields.resolutiondate,
                _versions,
                _components,
                issue.fields.description.replace('\r', '').replace('\n', ',').replace(' ', '').replace('"', "'"))
        #print _str
        _SQLcmd.append(_str)

    return _SQLcmd

def doHandler(befDay, edDay):

    print(">>> from %s to %s <<<" % (befDay, edDay))

    """连接数据库"""
    db = MySQLdb.connect(host="47.93.192.232", user="root", passwd="sw64419", db="nebula", charset='utf8')
    cur = db.cursor()

    """JIRA系统入口"""
    jira = JIRA('http://172.16.60.13:8080', basic_auth=('shenwei', 'sw64419'))

    _sqls = getIssue(jira, befDay, edDay)
    print(u'>>> Total number of Issue: %d' % len(_sqls))
    for _sql in _sqls:
        doSQLinsert(db, _sql, cur)
        #print _sql
    print(u'.完成')

    db.close()

if __name__ == '__main__':

    now = datetime.datetime.now()
    if now.isoweekday() == 1:
        """每周一执行，收集上一周的测试记录数据
        """
        befDay = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        edDay = datetime.datetime.now().strftime("%Y-%m-%d")
        doHandler(befDay, edDay)
