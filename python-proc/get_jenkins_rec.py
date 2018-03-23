#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# 获取 Jinkins（ FAST 3.0项目）记录
#
#

import jenkins, types, time
import MySQLdb, sys

reload(sys)
sys.setdefaultencoding('utf-8')

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
        db.commit()
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

def doIT(db, cur, url):

    server = jenkins.Jenkins(url, username='manager', password='8RP-KnN-V5s-BzA')
    print('> Jenkins version: %s' % server.get_version())

    _total = 0
    _insert = 0
    _update = 0

    jobs = server.get_all_jobs(folder_depth=2)
    for _job in jobs:
        items = server.get_job_info(_job['name'], fetch_all_builds=True)
        _first = items['firstBuild']
        if type(_first) is not types.NoneType:
            _first = int(_first['number'])
        _last = items['lastBuild']
        if type(_last) is not types.NoneType:
            _last = int(_last['number'])
        if type(_first) is not types.NoneType:
            for _i in range(_first,_last+1):
                #print _job,_i
                try:
                    unit = server.get_build_info(_job['name'], _i)
                except:
                    continue
                _time = float(unit['timestamp'])/1000

                _sql = 'select job_result,job_duration,job_estimatedDuration from jinkins_rec_t ' \
                       'where job_name="%s" and job_timestamp="%s"' % \
                       (unit['fullDisplayName'],
                        time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(_time)))
                _res = doSQL(cur, _sql)

                _total += 1

                if len(_res) > 0:
                    for _rec in _res:
                        if _rec[0] != unit['result']:
                            _sql = 'update jinkins_rec_t set job_result="%s" ' \
                                   'where job_name="%s" and job_timestamp="%s"' % (unit['result'],
                                                                                   unit['fullDisplayName'],
                                                                                   time.strftime('%Y-%m-%d %H:%M:%S',
                                                                                                 time.localtime(_time)))
                            #print _sql
                            doSQL(cur, _sql)
                            _update += 1
                    if _rec[1] != unit['duration']:
                        _sql = 'update jinkins_rec_t set job_duration="%s" ' \
                               'where job_name="%s" and job_timestamp="%s"' % (unit['duration'],
                                                                               unit['fullDisplayName'],
                                                                               time.strftime('%Y-%m-%d %H:%M:%S',
                                                                                             time.localtime(_time)))
                        # print _sql
                        doSQL(cur, _sql)
                        _update += 1
                    if _rec[2] != unit['estimatedDuration']:
                        _sql = 'update jinkins_rec_t set job_estimatedDuration="%s" ' \
                               'where job_name="%s" and job_timestamp="%s"' % (unit['estimatedDuration'],
                                                                               unit['fullDisplayName'],
                                                                               time.strftime('%Y-%m-%d %H:%M:%S',
                                                                                             time.localtime(_time)))
                        # print _sql
                        doSQL(cur, _sql)
                        _update += 1
                    continue

                _insert += 1
                _sql = 'insert into jinkins_rec_t(' \
                       'job_name,job_timestamp,job_queueId,job_result,job_description,' \
                       'job_duration,job_estimatedDuration,created_at,updated_at' \
                       ') values(' \
                       '"%s","%s","%s","%s","%s","%s","%s",now(),now())' % \
                       (unit['fullDisplayName'],
                        time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(_time)),
                        unit['queueId'],
                        unit['result'],
                        str(unit['description']).replace('"',"'"),
                        unit['duration'],
                        unit['estimatedDuration']
                        )
                #print _sql
                doSQLinsert(db, cur, _sql)
    print(": Total number: %d" % _total)
    if _insert > 0:
        print(": Inserted number: %d" % _insert)
    if _update > 0:
        print(": Updated number: %d" % _update)


if __name__ == '__main__':

    db = MySQLdb.connect(host="47.93.192.232", user="root", passwd="sw64419", db="nebula", charset='utf8')
    # db = MySQLdb.connect(host="172.16.101.117", user="root", passwd="123456", db="nebula", charset='utf8')
    cur = db.cursor()

    doIT(db, cur, 'http://172.16.74.169:32766')

    db.commit()
    db.close()
