# # -*- coding: utf-8 -*-
import pytest

from nebula.portal.app import create_app
from nebula.portal.models import db as real_db

# @pytest.fixture(scope='session')
# def app(request):
#     app = create_app()
#     app.testing = True
#     return app


@pytest.yield_fixture(scope='session')
def test_client(request):
    app = create_app()
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
    with app.test_request_context():
        yield app.test_client()


@pytest.fixture(scope='session')
def db(request):
    return real_db
