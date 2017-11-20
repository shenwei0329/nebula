from flexmock import flexmock
from flask_uploads import Upload, extensions
from . import TestCase


class TestWithoutResizer(TestCase):
    def test_upload_class_has_correct_attributes(self):
        assert hasattr(Upload, 'id')
        assert Upload.id == (
            'column',
            (('integer', [], {}),),
            {'autoincrement': True, 'primary_key': True}
        )
        assert hasattr(Upload, 'name')
        assert Upload.name == (
            'column',
            (('unicode', (255,), {}),),
            {'nullable': False}
        )
        assert hasattr(Upload, 'url')
        assert Upload.url == (
            'column',
            (('unicode', (255,), {}),),
            {'nullable': False}
        )

    def test_extensions_are_set_correctly(self):
        assert extensions.db is self.db
        assert isinstance(extensions.storage, self.Storage)
        assert extensions.resizer is None


class TestWithResizer(TestWithoutResizer):
    def setup_method(self, method):
        resizer = flexmock(
            sizes={
                'nail': (8, 19),
                'palm': (329, 192),
            }
        )
        TestWithoutResizer.setup_method(self, method, resizer)

    def test_upload_class_has_correct_attributes(self):
        TestWithoutResizer.test_upload_class_has_correct_attributes(self)

        assert hasattr(Upload, 'nail_name')
        assert Upload.nail_name == (
            'column',
            (('unicode', (255,), {}),),
            {}
        )

        assert hasattr(Upload, 'nail_url')
        assert Upload.nail_url == (
            'column',
            (('unicode', (255,), {}),),
            {}
        )

        assert hasattr(Upload, 'palm_name')
        assert Upload.palm_name == (
            'column',
            (('unicode', (255,), {}),),
            {}
        )

        assert hasattr(Upload, 'palm_url')
        assert Upload.palm_url == (
            'column',
            (('unicode', (255,), {}),),
            {}
        )

    def test_extensions_are_set_correctly(self):
        assert extensions.db is self.db
        assert isinstance(extensions.storage, self.Storage)
        assert extensions.resizer is self.resizer
