#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#

import jenkins, types, time, os, sys
import xml.dom.minidom
import MySQLdb

def doSQLinsert(db, cur, sql):
    """
    添加记录
    :param db: 数据库
    :param cur: 当前光标
    :param sql: SQL语句（INSERT）
    :return:
    """
    try:
        cur.execute(sql)
        #db.commit()
    except:
        print(">>>Err(mysql): %s" % sql)
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

def hasPackage(cur, package_name):
    """
    判断 package 是否已存在？
    :param cur: 数据源
    :param package_name: package名称
    :return: True/False
    """
    _sql = 'select count(*) from jenkins_coverage_t where class_name="%s"' % package_name
    _cnt = doSQLcount(cur, _sql)
    if _cnt > 0:
        return True
    else:
        return False

def hasPackageFile(cur, package_name, filename):
    """
    判断 package 是否已存在？
    :param cur: 数据源
    :param package_name: package名称
    :return: True/False
    """
    _sql = 'select count(*) from jenkins_coverage_t where class_name="%s" and filename="%s"' % (
        package_name, filename)
    _cnt = doSQLcount(cur, _sql)
    if _cnt > 0:
        return True
    else:
        return False

def getJenkinsCoverage(db, cur, server):

    jobs = server.get_all_jobs()

    _fns = []
    for job in jobs:
        """同步coverage文件"""
        _cmd = 'curl %s/ws/target/site/cobertura/coverage.xml --user %s:%s > %s-coverage.xml' % (job['url'],'manager','8RP-KnN-V5s-BzA', job['name'])
        print _cmd
        os.system(_cmd)

        _fn = '%s-coverage.xml' % job['name']
        _fns.append(_fn)

    """更新coverage数据"""
    for _fn in _fns:
        try:
            dom = xml.dom.minidom.parse(_fn)
            root = dom.documentElement
            nodes = root.getElementsByTagName('package')
            for node in nodes:

                if '.controller' not in node.getAttribute('name'):
                    continue

                print('> [%s]: line-rate=%s, branch-rate=%s, complexity=%s' % (
                    node.getAttribute('name'),
                    node.getAttribute('line-rate'),
                    node.getAttribute('branch-rate'),
                    node.getAttribute('complexity')))
                if not hasPackage(cur, node.getAttribute('name')):
                    _sql = 'insert into jenkins_coverage_t(' \
                           'class_name,filename,line_rate,branch_rate,complexity,created_at,updated_at) ' \
                           'values("%s","#","%s","%s","%s",now(),now())' % (
                        node.getAttribute('name'),
                        node.getAttribute('line-rate'),
                        node.getAttribute('branch-rate'),
                        node.getAttribute('complexity'))
                else:
                    _sql = 'update jenkins_coverage_t set ' \
                           'line_rate="%s",branch_rate="%s",complexity="%s",updated_at=now() ' \
                           'where class_name="%s" and filename="#"' % (
                        node.getAttribute('line-rate'),
                        node.getAttribute('branch-rate'),
                        node.getAttribute('complexity'),
                        node.getAttribute('name'))
                doSQLinsert(db, cur, _sql)

                classes = node.getElementsByTagName('class')
                for _class in classes:
                    print("\t<%s> line-rate=%s,branch-rate=%s,complexity=%s" % (
                        _class.getAttribute('filename'),
                        _class.getAttribute('line-rate'),
                        _class.getAttribute('branch-rate'),
                        _class.getAttribute('complexity')))
                    if not hasPackageFile(cur, node.getAttribute('name'), _class.getAttribute('filename')):
                        _sql = 'insert into jenkins_coverage_t(pj_id,' \
                               'class_name,filename,line_rate,branch_rate,complexity,created_at,updated_at) ' \
                               'values("%s","%s","%s","%s","%s","%s",now(),now())' % (
                                   "FAST",
                                   node.getAttribute('name'),
                                   _class.getAttribute('filename'),
                                   _class.getAttribute('line-rate'),
                                   _class.getAttribute('branch-rate'),
                                   _class.getAttribute('complexity'))
                    else:
                        _sql = 'update jenkins_coverage_t set ' \
                               'line_rate="%s",branch_rate="%s",complexity="%s",updated_at=now() ' \
                               'where class_name="%s" and filename="%s"' % (
                                   _class.getAttribute('line-rate'),
                                   _class.getAttribute('branch-rate'),
                                   _class.getAttribute('complexity'),
                                   node.getAttribute('name'),
                                   _class.getAttribute('filename'))
                    doSQLinsert(db, cur, _sql)
        except:
            print(">>> Error! <<<")
            continue


if __name__ == '__main__':

    if len(sys.argv) > 1:
        pj_id = sys.argv[1]
    else:
        pj_id = 'FAST'

    if pj_id == 'FAST':
        url = 'http://172.16.74.169:32766'
        user = 'manager'
        password = '8RP-KnN-V5s-BzA'
    elif pj_id == 'HUBBLE':
        url = 'http://172.16.60.12:8080/view/hubble2.0/'
        user = 'root'
        password = 'Is~admin'
    else:
        url = None

    if url is not None:

        db = MySQLdb.connect(host="47.93.192.232", user="root", passwd="sw64419", db="nebula", charset='utf8')
        # db = MySQLdb.connect(host="172.16.101.117", user="root", passwd="123456", db="nebula", charset='utf8')
        cur = db.cursor()
        server = jenkins.Jenkins(url, username=user, password=password)
        print('> Jenkins version: %s' % server.get_version())

        getJenkinsCoverage(db, cur, server)

        db.commit()
        db.close()
