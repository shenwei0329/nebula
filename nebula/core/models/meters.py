# -*- coding: utf-8 -*-
import logging
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Enum
from sqlalchemy import String
from sqlalchemy import Text

from nebula.core import constants
from nebula.core.models.mixins import CreatorOwnerMixin, URLMixin
from nebula.core.models.mixins import HasJobMixin
from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase


LOG = logging.getLogger(__name__)


class Meters(BASE, NebulaBase, CreatorOwnerMixin, HasJobMixin, URLMixin):

    """
    字段名称             字段类型        字段说明
    ===============     ============= ========================================
    ---------------     ------------- ----------------------------------------
    id                  int           主键
    type                enum          meter类型 1表示主机；2表示虚拟机
    meter_name          varchar(32)   显示名称
    meter_value         varchar(32)   值
    unit                varchar(32)   单位
    min_value           int           可设置的最小值
    max_value           int           可设置的最大值
    state               bool          可用状态
    description         text          描述
    create_at           datetime      创建时间
    update_at           varchar(39)   更新时间
    """

    __tablename__ = "alarm_meters"

    type        = Column(Enum(*constants.ALARM_METER_TYPE_ALL), nullable=False)
    meter_name  = Column(String(32), nullable=False)
    meter_value = Column(String(32), nullable=False)
    unit        = Column(String(32), nullable=False)
    min_value   = Column(Integer, nullable=True)
    max_value   = Column(Integer, nullable=True)
    state       = Column(Boolean, nullable=False, default=True)
    description = Column(Text(), nullable=True)
