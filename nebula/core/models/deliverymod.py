# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase

class DeliveryMod(BASE, NebulaBase):
    """
    """

    __tablename__ = 'delivery_t'

    id = Column(Integer, primary_key=True)
    EG_BH = Column(String(20))
    PD_DH = Column(String(20))
    PD_VERSION =  Column(String(10))
    DL_DATE =  Column(String(12))
    DL_STATE =  Column(String(40))

    @property
    def display_name(self):
        return self.id

    def to_dict(self):
        return dict(id=self.id,
                    EG_BH=self.EG_BH,
                    PD_DH=self.PD_DH,
                    PD_VERSION=self.PD_VERSION,
                    DL_DATE=self.DL_DATE,
                    DL_STATE=self.DL_STATE,
                    created_at=self.created_at,
                    )
