from StringIO import StringIO
from flexmock import flexmock
from flask_uploads import delete, save
from . import TestCase
from .test_save import FakeImage


class TestDelete(TestCase):
    def setup_method(self, method):
        if method == self.test_deletes_resized_images_from_storage:
            resizer = flexmock(sizes={'nail': (238, 23)})
            (resizer
                .should_receive('resize_image')
                .and_return({'nail': FakeImage('nail', 'jpg')}))
        else:
            resizer = None
        TestCase.setup_method(self, method, resizer)
        save(StringIO(u'cinna'), u'games')
        self.upload = self.committed_objects[0]
        self.added_objects[:] = []
        self.committed_objects[:] = []

    def test_deletes_from_storage(self):
        assert self.storage.exists(u'games')
        delete(self.upload)
        assert not self.storage.exists(u'games')

    def test_deletes_resized_images_from_storage(self):
        assert self.storage.exists(u'games_nail.jpg')
        delete(self.upload)
        assert not self.storage.exists(u'games_nail.jpg')

    def test_deletes_from_db(self):
        delete(self.upload)
        assert self.upload in self.deleted_objects

    def test_commits_deletion(self):
        delete(self.upload)
        assert self.upload in self.committed_objects
