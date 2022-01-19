from django.core.files.storage import get_storage_class

from recordtransfer.settings import UPLOAD_STORAGE_FOLDER

Storage = get_storage_class()

class OverwriteStorage(Storage):
    ''' Overwrites files in storage if they have the same name.

    Django's default method of storing files named the same thing is to append a unique suffix to
    the file name and saving the duplicate file there. This class overrides that behviour and
    overwrites any file being saved with a path that already exists.
    '''
    def _save(self, name, content):
        self.delete(name)
        return super()._save(name, content)

    def get_available_name(self, name, max_length=None):
        return name

class UploadedFileStorage(Storage):
    ''' Stores files in UPLOAD_STORAGE_FOLDER
    '''
    def __init__(self, **kwargs):
        kwargs['location'] = UPLOAD_STORAGE_FOLDER
        super().__init__(**kwargs)
