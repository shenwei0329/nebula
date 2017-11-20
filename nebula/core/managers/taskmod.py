# -*- coding: utf-8 -*-
"""
"""
import time

from nebula.core.managers.base import BaseManager
from nebula.core.models import DataElement

class TaskManager(BaseManager):

    def __init__(self, model):
        self.model = model

    def _get(self, name, session=None):
        return self.model_query(self.model, session=session, user_only=False).\
            filter_by(name=name).first()

    def get(self, name):
        return self._get(name)

    def get_by(self, session=None, **kwargs):
        return self.model_query(self.model, session=session, user_only=False).filter_by(**kwargs).first()

    def create(self, name, **kwargs):
        with self.transactional() as session:   # 做数据库事务
            if self.model == DataElement:
                etl = self.model(
                    TK_RW = name,
                    TK_XMBH = kwargs["TK_XMBH"],
                    TK_RWNR = kwargs["TK_RWNR"],
                    TK_ZXDZ = kwargs["TK_ZXDZ"],
                    TK_KSSJ = kwargs["TK_KSSJ"],
                    TK_JSSJ = kwargs["TK_JSSJ"],
                    TK_ZXR = kwargs["TK_ZXR"],
                    TK_BZ = kwargs["TK_BZ"],
                    TK_SQR = kwargs["TK_SQR"],
                    TK_RWZT = kwargs["TK_RWZT"],
                    TK_GZSJ = kwargs["TK_GZSJ"],
                )
            etl.save(session)
        return etl

    def update(self, name, **values):
        with self.transactional() as session:
            etl = self._get(name, session)
            etl.update(values)
        return etl

    def update_by_name(self, name, **values):
        retry = 5
        with self.transactional() as session:
            etl = self.get_by(session, name=name)
            i = 0
            while not etl:
                if i >= retry:
                    break
                i += 1
                time.sleep(2)
                etl = self.get_by(session, name=name)
            etl.update(values)
            etl.save(session)
        return etl

    def delete_by(self, **kwargs):
        with self.transactional() as session:
            session.query(self.model).filter_by(**kwargs).delete()

    def list(self):
        with self.transactional() as session:
            return session.query(self.model).filter_by()
