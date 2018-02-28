#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
from jira import JIRA
from jira.client import GreenHopper
import io

import types, json
import sys

options = {
    'server': 'http://172.16.60.13:8080',
}

jira = JIRA('http://172.16.60.13:8080', basic_auth=('shenwei', 'sw64419'))
gh = GreenHopper(options, basic_auth=('shenwei', 'sw64419'))
fd = io.open('date_desc.txt', 'w+', encoding='utf-8')


def _print(s):
    global fd

    fd.write(u"%s" % s)
    fd.write(u"\n")
    print(s)


def test(custom_name):
    # Fetch all fields
    allfields = jira.fields()
    # Make a map from field name -> field id
    nameMap = {field['name']: field['id'] for field in allfields}
    for _n in nameMap:
        print(u"> %s: %s" % (_n, nameMap[_n]))
    # Fetch an issue
    issue = jira.issue('FAST-3802')
    # You can now look up custom fields by name using the map
    getattr(issue.fields, nameMap[custom_name])


def printInf(issue):

    print dir(issue.fields)

    _f = dir(issue.fields)

    for __f in _f:
        if type(__f) is not types.NoneType:
            print __f

            _cmd = "print type(issue.fields.%s)" % (__f)
            exec (_cmd)

            _cmd = "if type(issue.fields.%s) is types.UnicodeType: print issue.fields.%s" % (__f, __f)
            exec (_cmd)

            _cmd = "if type(issue.fields.%s) is types.StringType: print issue.fields.%s" % (__f, __f)
            exec (_cmd)

            _cmd = "if type(issue.fields.%s) is types.ListType: print issue.fields.%s" % (__f, __f)
            exec (_cmd)

            _cmd = "if type(issue.fields.%s) is types.IntType: print issue.fields.%s" % (__f, __f)
            exec (_cmd)


def getIssue(jql, issue_name):

    _jql = jql + ' AND issue=' + issue_name
    return jira.search_issues(_jql, maxResults=1)[0]


def getIssues(jql, issue_name):

    total = 0
    while True:
        issues = jira.search_issues(jql, maxResults=100, startAt=total)
        for issue in issues:
            if "%s" % issue == issue_name:
                return issue
        if len(issues) == 100:
            total += 100
        else:
            break
    return None


def showIt(issue):
    watcher = jira.watchers(issue)
    print("Issue has {} watcher(s)".format(watcher.watchCount))
    for watcher in watcher.watchers:
        print(u'%s' % watcher)
    # watcher is instance of jira.resources.User:
    print(u'%s' % watcher.emailAddress)

def showField(jql, issue_name):

    # Fetch all fields
    allfields = jira.fields()
    # Make a map from field name -> field id
    # nameMap = {field['name']: field['id'] for field in allfields}
    idMap = {field['id']: field['name'] for field in allfields}

    issue = getIssue(jql, issue_name)
    if issue is not None:

        # showIt(issue)
        print issue.raw.keys()
        for field_name in issue.raw['fields']:
            print "Name:", "%-20s" % field_name,\
                u'%-22s' % idMap[field_name],\
                "\n\t==>", u'%s' % issue.raw['fields'][field_name]

def dispGreenHopper(gh):
    _f = gh.fields()
    for __f in _f:
        __cns = __f['clauseNames']
        _print('-' * 8)
        for _n in __cns:
            _print(u"name: %s" % _n)
        _print(u"id: %s" % __f['id'])
        _print(u"name: %s" % __f['name'])


def main():
    global gh

    # print dir(gh.sprints({}))
    # dispGreenHopper(gh)
    issue = 'FAST-' + sys.argv[1]
    # showField('project=FAST', issue)
    jql = "issue in  childrenOfParentRequirement('%s')" % issue
    # jql = "issue in hasRequirements() and type='task'"
    # print jql
    tot = 0
    while True:
        issues = jira.search_issues(jql, maxResults=100, startAt=tot)
        for issue in issues:
            print issue.key
        if len(issues) == 100:
            tot += 100
        else:
            break

    # showField('project=FAST AND issuetype=task', 'FAST-3819')
    # test("FAST-3802")


if __name__ == '__main__':

    if len(sys.argv) > 1:
        main()
    fd.close()
