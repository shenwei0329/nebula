#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
from jira import JIRA
import types, json, sys

jira = JIRA('http://172.16.60.13:8080',basic_auth=('shenwei','sw64419'))

"""
projects = jira.projects()
for _proj in projects:
    print _proj

"""
"""
print dir(issue)
['JIRA_BASE_URL', '_IssueFields', '_READABLE_IDS', '__class__', '__delattr__', '__dict__', '__doc__', '__eq__', 
'__format__', '__getattr__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', 
'__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_base_url', 
'_default_headers', '_get_url', '_load', '_options', '_parse_raw', '_resource', '_session', 'add_field_value', 
'delete', 'expand', 'fields', 'find', 'id', 'key', 'permalink', 'raw', 'self', 'update']

print dir(issue.fields)
['__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', u'aggregateprogress', u'aggregatetimeestimate', u'aggregatetimeoriginalestimate', u'aggregatetimespent', u'assignee', u'components', u'created', u'creator', u'customfield_10200', u'customfield_10300', u'customfield_10301', u'customfield_10302', u'customfield_10303', u'customfield_10400', u'customfield_10500', u'customfield_10501', u'customfield_10502', u'
customfield_10503', u'customfield_10504', u'customfield_10505', u'customfield_10506', u'customfield_10507', u'customfield_10508', u'customfield_10509', u'customfield_10510', u'customfield_10511', u'customfield_10800', u'customfield_11001', u'customfield_11002', u'customfield_11100', u'customfield_11200',
 u'customfield_11300', u'customfield_11304', u'customfield_11400', u'customfield_11402', u'customfield_11403', u'customfield_11404', u'customfield_11405', u'customfield_11406', u'customfield_11407', u'description', u'duedate', u'environment', u'fixVersions', u'issuelinks', u'issuetype', u'labels', u'last
Viewed', u'priority', u'progress', u'project', u'reporter', u'resolution', u'resolutiondate', u'status', u'subtasks', u'summary', u'timeestimate', u'timeoriginalestimate', u'timespent', u'updated', u'versions', u'votes', u'watches', u'workratio']

_f = dir(issue.fields)

for __f in _f:
    if type(__f) is not types.NoneType:

        print __f

        _cmd = "if type(issue.fields.%s) is types.ListType: print issue.fields.%s" % (__f,__f)
        exec(_cmd)

        _cmd = "if type(issue.fields.%s) is types.IntType: print issue.fields.%s" % (__f, __f)
        exec (_cmd)
"""

def getIssue(bg_date, ed_date):

    Task = {}
    issues = jira.search_issues('project in (HBLE, WHIT, FASTT, AP) AND '
                                'issuetype in (Improvement, Bug, 缺陷) AND updated >= %s AND updated <= %s' %
                                (bg_date,ed_date), maxResults=10000)
    _n = 0
    for issue in issues:

        watcher = jira.watchers(issue)
        _user = {}
        for watcher in watcher.watchers:
            if watcher.active:
                _user['alias'] = watcher.name
                _user['name'] = watcher.displayName
                _user['email'] = watcher.emailAddress

        print dir(issue.fields.project)
        """
['JIRA_BASE_URL', '_READABLE_IDS', '__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattr__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_b
ase_url', '_default_headers', '_get_url', '_load', '_options', '_parse_raw', '_resource', '_session', 'avatarUrls', 'delete', 'find', 'id', 'key', 'name', 'raw', 'self', 'update']
        """
        print("[%s]-%s" % (str(issue),issue.fields.summary))
        print(u'%s' % issue.fields.status)
        print(u'%s.%s.%s' % (_user['name'], _user['alias'], _user['email']))
        print(u'%s' % issue.fields.description)
        print u'%s' % issue.fields.priority
        print u'%s' % issue.fields.project.key
        print u'%s' % issue.fields.project.name
        print issue.fields.created
        print issue.fields.updated
        _n += 1
        break
    return _n

_n = getIssue(sys.argv[1],sys.argv[2])
print _n
