数据库模型
===============

Model只包含单纯的数据库定义, 包括表名 字段类型和约束关系.


Model目录
------------

``nebula/code/nebula/core/models``


Model基础类
------------

#. nebula.core.models.model_base.BASE

    .. autoclass:: nebula.core.models.model_base.BASE

#. nebula.core.models.model_base.NebulaBase

    .. autoclass:: nebula.core.models.model_base.NebulaBase

#. nebula.core.models.mixins.CreatorOwnerMixin

    .. autoclass:: nebula.core.models.mixins.CreatorOwnerMixin


Model定义示例::

    class VirtualrouterNat(BASE, NebulaBase, CreatorOwnerMixin):
        """Represents a neutron virtualrouter nat.
        *数据卷模型字段定义列表*


        ======================== ============= ==========================================
        字段名称                   字段类型        字段说明
        ======================== ============= ==========================================
        id                       int           主键
        virtualrouter_nat_uuid   varchar(36)   虚拟路由器端口映射资源UUID
        proto                    enum          网络传输协议，为TCP、UDP、ICMP或IP之一
        src_port                 int           虚拟路由器端口映射源端口
        dest_port                int           虚拟路由器端口映射目的端口
        dest_ip                  varchar(39)   虚拟路由器端口映射目的地址
        publicip_id              int           虚拟路由器绑定公网IP外键
        user_id                  int           用户外键
        ======================== ============= ==========================================
        """

        __tablename__ = "virtualrouter_nats"                          # 定义数据库表名

        virtualrouter_nat_uuid = Column(UUID(), index=True)
        proto = Column(Enum(constants.NET_PROTOCOL_TCP,
                            constants.NET_PROTOCOL_UDP,
                            constants.NET_PROTOCOL_ICMP,
                            constants.NET_PROTOCOL_IP),
                       default=constants.NET_PROTOCOL_IP)
        src_port = Column(Integer, nullable=True)
        dest_ip = Column(IPAddress, nullable=False)
        dest_port = Column(Integer, nullable=True)
        publicip_id = Column(Integer,                                  # 定义外键
                             ForeignKey('virtualrouter_publicips.id',
                                        ondelete='CASCADE'))

        publicip = relationship('VirtualrouterPublicIP',               # 定义外键属性
                                backref=backref('virtualrouter_nats',
                                                cascade='all, delete-orphan',
                                                passive_deletes=True),
                                foreign_keys=publicip_id)


修改数据库
------------

目前还未集成Database Migration工具, 修改模型定义后, 需要手动修改数据库.

在 ``nebula/code/`` 目录下, 执行

>>> invoke db.dump

查找修改后数据库定义语句, 手动在数据库执行.
