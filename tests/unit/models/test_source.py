# -*- coding:utf-8 -*-
from nebula.portal.models import Source


def test_create_source(db):
    metric = Source.get_or_create('test.huamon.com')
    another_metric = Source.get_or_create('test.huamon.com')
    assert metric.name == another_metric.name
