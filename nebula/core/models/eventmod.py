# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase

class EventMod(BASE, NebulaBase):
    """
    """

    __tablename__ = 'event_t'

    id = Column(Integer, primary_key=True)
    EV_NAME =  Column(String(80))
    EV_BH = Column(String(10))
    EV_STATE = Column(String(10))

    @property
    def display_name(self):
        return self.EV_NAME

    def to_dict(self):
        return dict(id=self.id,
                    name=self.EV_NAME,
                    number=self.EV_BH,
                    state=self.EV_STATE,
                    created_at=self.created_at,
                    )
