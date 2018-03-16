#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#   MySQL处理机
#   ===========
#

class SqlService:

    def __init__(self, db):
        self.db = db
        self.cur = db.cursor()

    def insert(self, _sql):
        if self.cur is None:
            return
        try:
            self.cur.execute(_sql)
            self.db.commit()
        except:
            self.db.rollback()

    def count(self, _sql):
        if self.cur is None:
            return 0
        _n = 0
        try:
            self.cur.execute(_sql)
            _result = self.cur.fetchone()
            _n = _result[0]
            if _n is None:
                _n = 0
        except:
            _n = 0
        finally:
            return int(_n)

    def do(self, _sql):
        if self.cur is None:
            return
        self.cur.execute(_sql)
        return self.cur.fetchall()


