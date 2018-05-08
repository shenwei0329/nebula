# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase

class EtlDir(BASE, NebulaBase):
    """
    资源目录
        ID：主键
        名称
        描述
        命令
    """

    __tablename__ = 'etl_dir'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    dir = Column(String(80))            # UUID目录名称
    desc = Column(String(255))          # 资源目录说明，如”SPARK资源“

    @property
    def display_name(self):
        return self.name

    def to_dict(self):
        return dict(name=self.name,
                    desc=self.desc,
                    dir=self.dir,
                    created_at=self.created_at,
                    )

class EtlMod(BASE, NebulaBase):

    __tablename__ = 'etl_mod'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    d_id = Column(Integer)              # 所归属的资源目录的ID
    desc = Column(String(255))          # 资源描述，如需要的运行环境等
    r_name = Column(String(80))         # 资源名称
    filename = Column(String(80))       # UUID名称
    version = Column(String(80))        # 版本
    cmd = Column(String(200))           # 资源的运行脚本

    @property
    def display_name(self):
        return self.name

    def to_dict(self):
        return dict(name=self.name,
                    desc=self.desc,
                    r_name=self.r_name,
                    filename=self.filename,
                    version=self.version,
                    cmd=self.cmd,
                    created_at=self.created_at,
                    )

class EtlServer(BASE, NebulaBase):

    __tablename__ = 'etl_server'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    desc = Column(String(255))      # 描述服务器，如master服务器，或ETL服务器等
    url = Column(String(200))       # 服务器访问入口
    status = Column(Integer)        # 可连接状态，1:是；0:否

    @property
    def display_name(self):
        return self.name

    def to_dict(self):
        return dict(name=self.name,
                    desc=self.desc,
                    url=self.url,
                    status=self.status,
                    created_at=self.created_at,
                    )

class EtlTask(BASE, NebulaBase):
    """
    构建ETL任务表项
        id
        name: 名称（作业命名，唯一性）
        mod：模型
        server：ETL服务器
        status：运行状态
    """

    __tablename__ = 'etl_task'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    mod = Column(String(80))
    server = Column(String(80))
    status = Column(String(16))

    @property
    def display_name(self):
        return self.name

    def to_dict(self):
        return dict(name=self.name,
                    mod=self.mod,
                    server=self.server,
                    status=self.status,
                    created_at=self.created_at,
                    )

class EtlJob(BASE, NebulaBase):
    """
    构建ETL作业表项
        id
        name: 名称（作业命名，唯一性）
        mod：模型
        server：ETL服务器
        schedule：调度策略（ 分钟[0~59] 小时[0~23] 日期[1~31] 月份[1~12] 星期[0~6]）
        status：运行状态
    """

    __tablename__ = 'etl_job'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    mod = Column(String(80))
    server = Column(String(80))
    schedule = Column(String(80))
    status = Column(String(16))

    @property
    def display_name(self):
        return self.name

    def to_dict(self):
        return dict(name=self.name,
                    mod=self.mod,
                    server=self.server,
                    schedule=self.schedule,
                    status=self.status,
                    created_at=self.created_at,
                    )
