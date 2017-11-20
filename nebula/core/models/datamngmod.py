# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase

class DataElement(BASE, NebulaBase):
    """
    资源目录
        ID：主键
        名称
        描述
        命令
    """

    __tablename__ = 'data_element_t'

    id = Column(Integer, primary_key=True)
    keyid = Column(String(80), unique=True)
    val = Column(String(80))
    val_desc = Column(String(256))
    val_type = Column(String(80))

    @property
    def display_name(self):
        return self.name

    def to_dict(self):
        return dict(keyid=self.keyid,
                    val=self.val,
                    desc=self.val_desc,
                    type=self.val_type,
                    created_at=self.created_at,
                    )
