from django.core.files.uploadhandler import FileUploadHandler
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings

import os
import tempfile


class PersistentUploadedFile(UploadedFile):
    """
    A file uploaded to a temporary location that must be removed manually.
    """
    def __init__(self, name, content_type, size, charset, content_type_extra=None):
        _, ext = os.path.splitext(name)
        temporaryfile = tempfile.NamedTemporaryFile(suffix='.upload' + ext, dir=settings.FILE_UPLOAD_TEMP_DIR, delete=False)
        super().__init__(temporaryfile, name, content_type, size, charset, content_type_extra)

    @property
    def path(self):
        return self.file.name

    def close(self):
        try:
            return self.file.close()
        except FileNotFoundError:
            # The file was moved or deleted before the tempfile could unlink
            # it. Still sets self.file.close_called and calls
            # self.file.file.close() before the exception.
            pass


class PersistentFileUploadHandler(FileUploadHandler):
    """
    Upload handler that streams data into a temporary file that must be removed
    manually.
    """
    def new_file(self, *args, **kwargs):
        """
        Create the file object to append to as data is coming in.
        """
        super().new_file(*args, **kwargs)
        self.file = PersistentUploadedFile(self.file_name, self.content_type, 0,
            self.charset, self.content_type_extra)

    def receive_data_chunk(self, raw_data, start):
        self.file.write(raw_data)

    def file_complete(self, file_size):
        self.file.seek(0)
        self.file.size = file_size
        return self.file
