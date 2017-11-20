# -*- coding: utf-8 -*-
from flask import url_for


class TestMetricAPI(object):

    def test_post(self, test_client):
        self.url = url_for('portal.metrics_api')
        rv = test_client.post(self.url, data={'source':'test', 'name':'test', 'value':1})
        assert rv.status_code == 200

    def test_list(self, test_client):
        self.url = url_for('portal.metrics_api')
        rv = test_client.get
        assert rv.status_code == 200
