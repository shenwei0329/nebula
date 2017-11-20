# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase

class MemberMod(BASE, NebulaBase):
    """
    员工
        ID：主键
        名称
        员工号
        状态
    """

    __tablename__ = 'member_t'

    id = Column(Integer, primary_key=True)
    MM_XM = Column(String(80), unique=True)
    MM_GH = Column(String(20))
    MM_ZT = Column(String(20))

    @property
    def display_name(self):
        return self.YG_NAME

    def to_dict(self):
        return dict(id=self.id,
                    name=self.MM_XM,
                    number=self.MM_GH,
                    state=self.MM_ZT,
                    updated_at=self.updated_at,
                    )
