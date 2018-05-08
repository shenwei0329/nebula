# -*- coding: utf-8 -*-
from nebula.portal.models import Metric


class TestMetric(object):

    def _compare_value(self, db, source_name, name, value):
        obj = Metric.create_metric(source_name, name, value)

        db.session.add(obj)
        db.session.flush()
        db.session.refresh(obj)

        assert obj.source.name == source_name
        assert obj.name == name
        assert isinstance(obj.lastest_value, float)
        assert obj.lastest_value == float(value)
        assert obj.updated_at is not None

    def test_create_metric(self, db):
        source_name = 'test.huamon.com'
        name = 'test_float'
        value = 1.0
        self._compare_value(db, source_name, name, value)

        name = 'test_int'
        value = 10
        self._compare_value(db, source_name, name, value)

        name = 'test_boolean'
        value = True
        self._compare_value(db, source_name, name, value)


