# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase

class EnginerringMod(BASE, NebulaBase):
    """
    """

    __tablename__ = 'enginerring_t'

    id = Column(Integer, primary_key=True)
    EG_NAME =  Column(String(80))
    EG_BH = Column(String(40))
    EG_STATE = Column(String(20))
    EG_PJ_BH =  Column(String(40))
    EG_SITE =  Column(String(200))
    EG_ENV =  Column(String(200))

    @property
    def display_name(self):
        return self.EG_NAME

    def to_dict(self):
        return dict(id=self.id,
                    name=self.EG_NAME,
                    number=self.EG_BH,
                    state=self.EG_STATE,
                    project=self.EG_PJ_BH,
                    site=self.EG_SITE,
                    env=EG_ENV,
                    created_at=self.created_at,
                    )
