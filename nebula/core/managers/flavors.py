# -*- coding: utf-8 -*-

from nebula.core import models
from nebula.core.db import exception as db_exc
from nebula.core.db import session as db_session

from .base import BaseManager


class FlavorManager(BaseManager):

    def create_or_get(self, context, name, vcpus, ram, root_gb):
        """创建或获取规格."""
        with self.transactional() as session:
            values = dict(
                name=name,
                vcpus=vcpus,
                memory_mb=ram * 1024,
                root_gb=root_gb
            )
            query = session.query(models.Flavor)
            flavor_ref = query.filter_by(name=name).first()
            if not flavor_ref:
                flavor_ref = models.Flavor()
                flavor_ref.update(values)
                flavor_ref.save(session)
            return flavor_ref
    
    def _get(self, context, id, session=None):
        return self.model_query(context, models.Flavor, session=session, user_only=False).get(id)

    def get(self, context, id):
        return self._get(context, id)
