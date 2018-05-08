# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase

class ReportMod(BASE, NebulaBase):
    """
    报表：周、月、季度、年
    """

    __tablename__ = 'report_t'

    id = Column(Integer, primary_key=True)
    file_hash = Column(String(120), unique=True)
    report_date = Column(String(20))
    group = Column(String(100))
    grp_member_num = Column(Integer)
    plan_hours = Column(Integer)
    active_hours = Column(Integer)
    extra_hours = Column(Integer)
    leave_hours = Column(Integer)

    @property
    def display_name(self):
        return self.file_hash

    def to_dict(self):
        return dict(id=self.id,
                    file_hash = self.file_hash,
                    report_date = self.report_date,
                    group = self.group,
                    grp_member_num = self.grp_member_num,
                    plan_hours = self.plan_hours,
                    active_hours = self.active_hours,
                    extra_hours = self.extra_hours,
                    leave_hours = self.leave_hours,
                    created_at=self.created_at,
                    )
