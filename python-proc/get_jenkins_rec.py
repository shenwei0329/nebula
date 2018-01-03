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

def doIT(db, cur, url):

    server = jenkins.Jenkins(url)
    print('> Jenkins version: %s' % server.get_version())

    _total = 0
    _insert = 0

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

                unit = server.get_build_info(_job['name'], _i)
                _time = float(unit['timestamp'])/1000

                _sql = 'select count(*) from jinkins_rec_t where job_name="%s" and job_timestamp="%s"' % \
                       (unit['fullDisplayName'],
                        time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(_time)))
                _n = doSQLcount(cur, _sql)

                _total += 1
                if _n >0:
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
    if _insert>0:
        print(": Inserted number: %d" % _insert)

if __name__ == '__main__':

    db = MySQLdb.connect(host="47.93.192.232", user="root", passwd="sw64419", db="nebula", charset='utf8')
    cur = db.cursor()

    doIT(db, cur, 'http://172.16.74.169:32766')

    db.close()
