# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase

class UpFileMod(BASE, NebulaBase):
    """
    资源目录
        ID：主键
        名称
        描述
        命令
    """

    __tablename__ = 'upfile_t'

    id = Column(Integer, primary_key=True)
    f_hash = Column(String(80), unique=True)
    filename =  Column(String(200))
    desc = Column(String(80))
    version = Column(String(80))

    @property
    def display_name(self):
        return self.name

    def to_dict(self):
        return dict(id=self.id,
                    filename=self.filename,
                    desc=self.desc,
                    version=self.version,
                    f_hash=self.f_hash,
                    created_at=self.created_at,
                    )
