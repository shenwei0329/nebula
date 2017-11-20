from flexmock import flexmock
from flask.ext.storage import MockStorage
from flask_uploads import init


class TestCase(object):
    added_objects = []
    committed_objects = []
    created_objects = []
    deleted_objects = []

    def setup_method(self, method, resizer=None):
        init(db_mock, MockStorage, resizer)
        self.db = db_mock
        self.Storage = MockStorage
        self.storage = MockStorage()
        self.resizer = resizer

    def teardown_method(self, method):
        # Empty the stacks.
        TestCase.added_objects[:] = []
        TestCase.committed_objects[:] = []
        TestCase.created_objects[:] = []
        TestCase.deleted_objects[:] = []


class MockModel(object):
    def __init__(self, **kw):
        TestCase.created_objects.append(self)
        for key, val in kw.iteritems():
            setattr(self, key, val)


db_mock = flexmock(
    Column=lambda *a, **kw: ('column', a, kw),
    Integer=('integer', [], {}),
    Unicode=lambda *a, **kw: ('unicode', a, kw),
    Model=MockModel,
    metadata=flexmock(tables={}),
    session=flexmock(
        add=TestCase.added_objects.append,
        commit=lambda: TestCase.committed_objects.extend(
            TestCase.added_objects + TestCase.deleted_objects
        ),
        delete=TestCase.deleted_objects.append,
    ),
)
