# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase

class TaskMod(BASE, NebulaBase):
    """
    """

    __tablename__ = 'task_t'

    id = Column(Integer, primary_key=True)
    TK_XMBH = Column(String(20))
    TK_RW = Column(String(80))
    TK_RWNR = Column(String(256))
    TK_ZXDZ = Column(String(160))
    TK_KSSJ = Column(String(40))
    TK_JSSJ = Column(String(40))
    TK_ZXR = Column(String(40))
    TK_BZ = Column(String(160))
    TK_SQR = Column(String(40))
    TK_RWZT = Column(String(40))
    TK_GZSJ = Column(String(40))

    @property
    def display_name(self):
        return self.TK_RW

    def to_dict(self):
        return dict(id=self.id,
                    TK_XMBH = self.TK_XMBH,
                    TK_RW = self.TK_RW,
                    TK_RWNR = self.TK_RWNR,
                    TK_ZXDZ = self.TK_ZXDZ,
                    TK_KSSJ = self.TK_KSSJ,
                    TK_JSSJ = self.TK_JSSJ,
                    TK_ZXR = self.TK_ZXR,
                    TK_BZ = self.TK_BZ,
                    TK_SQR = self.TK_SQR,
                    TK_RWZT = self.TK_RWZT,
                    TK_GZSJ = self.TK_GZSJ,
                    created_at=self.created_at,
                    )
