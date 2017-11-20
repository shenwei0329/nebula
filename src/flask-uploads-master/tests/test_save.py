from StringIO import StringIO
from flexmock import flexmock
import flask_uploads.functions as funcs
from flask_uploads import save, save_file, save_images, init
from . import TestCase

save, save_file, save_images


class FakeImage(object):
    def __init__(self, name, ext):
        self.name = name
        self.ext = ext

    def save(self, io, format=None):
        io.write('%s saved as %s' % (self.name, format))


class StorageTestCase(TestCase):
    def teardown_method(self, method):
        self.storage.empty()
        TestCase.teardown_method(self, method)


class TestSaveFile(StorageTestCase):
    def test_saves_data_to_storage(self):
        save_file(u'jackfile', u'bauercontent')
        assert self.storage.exists(u'jackfile')
        assert self.storage.open(u'jackfile').read() == u'bauercontent'

    def _assert_model_added_to_collection(self, attr):
        save_file(u'jackfile', u'bauercontent')
        assert len(getattr(self, attr)) == 1
        obj = getattr(self, attr)[0]
        assert obj.name == u'jackfile'
        assert obj.url == self.storage.url(u'jackfile')

    def test_creates_upload(self):
        self._assert_model_added_to_collection('created_objects')

    def test_adds_upload_to_db(self):
        self._assert_model_added_to_collection('added_objects')

    def test_commits_upload_to_db(self):
        self._assert_model_added_to_collection('committed_objects')


class TestSaveImages(StorageTestCase):
    def setup_method(self, method):
        StorageTestCase.setup_method(self, method)
        self.images = {
            'nail': FakeImage('nail', 'jpg'),
            'palm': FakeImage('palm', 'png'),
        }

    def test_saves_data_and_images_to_storage(self):
        save_images(u'jackfile', u'bauercontent', self.images)

        assert self.storage.exists(u'jackfile')
        assert self.storage.open(u'jackfile').read() == u'bauercontent'

        assert self.storage.exists(u'jackfile_nail.jpg')
        assert (
            self.storage.open(u'jackfile_nail.jpg').read() ==
            u'nail saved as jpg'
        )

        assert self.storage.exists(u'jackfile_palm.png')
        assert (
            self.storage.open(u'jackfile_palm.png').read() ==
            u'palm saved as png'
        )

    def _assert_model_added_with_attributes(self, attr):
        save_images(u'jackfile', u'bauercontent', self.images)
        assert len(getattr(self, attr)) == 1
        obj = getattr(self, attr)[0]

        assert obj.name == u'jackfile'
        assert obj.url == self.storage.url(u'jackfile')

        assert obj.nail_name == u'jackfile_nail.jpg'
        assert obj.nail_url == self.storage.url(u'jackfile_nail.jpg')

        assert obj.palm_name == u'jackfile_palm.png'
        assert obj.palm_url == self.storage.url(u'jackfile_palm.png')

    def test_creates_upload(self):
        self._assert_model_added_with_attributes('created_objects')

    def test_adds_upload_to_db(self):
        self._assert_model_added_with_attributes('added_objects')

    def test_commits_upload_to_db(self):
        self._assert_model_added_with_attributes('committed_objects')


class TestSave(StorageTestCase):
    def setup_method(self, method):
        StorageTestCase.setup_method(self, method)

        def savefile(name, content):
            self.save_file_args = (name, content)

        def saveimages(name, content, images):
            self.save_images_args = (name, content, images)

        self.save_file_args = self.save_images_args = None
        self._save_file = save_file
        self._save_images = save_images
        funcs.save_file = savefile
        funcs.save_images = saveimages

    def teardown_method(self, method):
        funcs.save_file = save_file
        funcs.save_images = save_images
        StorageTestCase.teardown_method(self, method)

    def test_calls_save_file_without_resizer(self):
        init(self.db, self.Storage)
        save(StringIO(u'bauercontent'), u'jackfile')
        assert self.save_file_args == (u'jackfile', u'bauercontent')

    def test_calls_save_file_when_resizing_raises_ioerror(self):
        def raise_ioerror(*args, **kwargs):
            raise IOError
        init(
            self.db,
            self.Storage,
            flexmock(
                sizes={'nail': (23, 49)},
                resize_image=raise_ioerror,
            )
        )
        save(StringIO(u'bauercontent'), u'jackfile')
        assert self.save_file_args == (u'jackfile', u'bauercontent')

    def test_calls_save_images_when_resizing_works(self):
        images = object()
        init(
            self.db,
            self.Storage,
            flexmock(
                sizes={
                    'nail': (38, 12),
                },
                resize_image=lambda x: images
            )
        )
        save(StringIO(u'bauercontent'), u'jackfile')
        assert self.save_images_args == (u'jackfile', u'bauercontent', images)
