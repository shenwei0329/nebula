# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from nebula.core.models.model_base import BASE
from nebula.core.models.model_base import NebulaBase

class ReportRecMod(BASE, NebulaBase):
    """
    报表：周、月、季度、年
    """

    __tablename__ = 'report_rec_t'

    id = Column(Integer, primary_key=True)
    file_hash = Column(String(120), unique=True)
    PJ_BH = Column(String(80))
    task_type = Column(String(200))
    task_name = Column(String(120))
    task_desc = Column(String(300))
    start_date = Column(String(20))
    end_date = Column(String(20))
    comp_rate = Column(String(20))
    comp_desc = Column(String(300))
    task_risk = Column(String(300))
    task_cost = Column(String(20))
    task_member = Column(String(80))
    task_note = Column(String(200))
    group = Column(String(100))

    @property
    def display_name(self):
        return self.file_hash

    def to_dict(self):
        return dict(id=self.id,
                    file_hash = self.file_hash,
                    project_number=self.PJ_BH,
                    task_type = self.task_type,
                    task_name = self.task_name,
                    task_desc = self.task_desc,
                    start_date = self.start_date,
                    end_date = self.end_date,
                    comp_rate = self.comp_rate,
                    comp_desc = self.comp_desc,
                    task_risk = self.task_risk,
                    task_cost = self.task_cost,
                    task_member = self.task_member,
                    task_note = self.task_note,
                    group = self.group,
                    created_at=self.created_at,
                    )
