# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase

class ProjectMod(BASE, NebulaBase):
    """
    """

    __tablename__ = 'project_t'

    id = Column(Integer, primary_key=True)
    PJ_XMBH = Column(String(20), unique=True)
    PJ_XMMC = Column(String(80))
    PJ_XMFZR = Column(String(80))
    PJ_LXSJ = Column(String(40))
    PJ_KSSJ = Column(String(40))
    PJ_JSSJ = Column(String(40))
    PJ_XMJJ = Column(String(256))
    PJ_XMYS = Column(String(40))
    PJ_XMZT = Column(String(40))
    PJ_XMXZ = Column(String(40))
    PJ_JFSJ = Column(String(40))
    PJ_SJFY = Column(String(40))
    PJ_MBYH = Column(String(160))

    @property
    def display_name(self):
        return self.PJ_XMMC

    def to_dict(self):
        return dict(id=self.id,
                    PJ_XMMC = self.PJ_XMMC,
                    PJ_XMBH = self.PJ_XMBH,
                    PJ_XMFZR = self.PJ_XMFZR,
                    PJ_LXSJ = self.PJ_LXSJ,
                    PJ_KSSJ = self.PJ_KSSJ,
                    PJ_JSSJ = self.PJ_JSSJ,
                    PJ_XMJJ = self.PJ_XMJJ,
                    PJ_XMYS = self.PJ_XMYS,
                    PJ_XMZT = self.PJ_XMZT,
                    PJ_XMXZ = self.PJ_XMXZ,
                    PJ_JFSJ = self.PJ_JFSJ,
                    PJ_SJFY = self.PJ_SJFY,
                    PJ_MBYH = self.PJ_MBYH,
                    created_at=self.created_at,
                    )
