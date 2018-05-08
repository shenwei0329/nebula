# -*- coding: utf-8 -*-
"""
    2015.9.1 shenwei @ChengDu

    在创建表记录时追加 创建日期 和 修改日期
    在修改表记录时要更改 修改日期

"""
import time

from nebula.core.managers.base import BaseManager
from nebula.core.models import MemberMod

class DeliveryManager(BaseManager):

    def __init__(self, model):
        self.model = model

    def _get(self, id, session=None):
        return self.model_query(self.model, session=session, user_only=False).\
            filter_by(id=id).first()

    def get(self, name):
        return self._get(name)

    def get_by(self, session=None, **kwargs):
        return self.model_query(self.model, session=session, user_only=False).filter_by(**kwargs).first()

    def create(self, name, **kwargs):
        with self.transactional() as session:   # 做数据库事务
            if self.model == UpFileMod:
                etl = self.model(
                    EG_BH=name,
                    PD_DH=kwargs["PD_DH"],
                    PD_VERSION=kwargs["PD_VERSION"],
                    DL_DATE=kwargs["DL_DATE"],
                )
            etl.save(session)
        return etl

    def update(self, name, **values):
        with self.transactional() as session:
            etl = self._get(name, session)
            etl.update(values)
        return etl

    def update_by_name(self, id, **values):
        retry = 5
        with self.transactional() as session:
            etl = self.get_by(session, id=id)
            i = 0
            while not etl:
                if i >= retry:
                    break
                i += 1
                time.sleep(2)
                etl = self.get_by(session, id=id)
            etl.update(values)
            etl.save(session)
        return etl

    def delete_by(self, **kwargs):
        with self.transactional() as session:
            session.query(self.model).filter_by(**kwargs).delete()

    def list(self):
        with self.transactional() as session:
            return session.query(self.model).filter_by()
