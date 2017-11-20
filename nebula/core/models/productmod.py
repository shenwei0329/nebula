# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase

class ProductMod(BASE, NebulaBase):
    """
    """

    __tablename__ = 'product_t'

    id = Column(Integer, primary_key=True)
    PD_MC = Column(String(80))
    PD_DH = Column(String(40))
    PD_LX = Column(String(40))
    PD_BBH = Column(String(40))
    PD_FBSJ = Column(String(40))

    @property
    def display_name(self):
        return self.PD_MC

    def to_dict(self):
        return dict(id=self.id,
                    PD_MC = self.PD_MC,
                    PD_DH = self.PD_DH,
                    PD_LX = self.PD_LX,
                    PD_BBH = self.PD_BBH,
                    PD_FBSJ = self.PD_FBSJ,
                    created_at=self.created_at,
                    )
