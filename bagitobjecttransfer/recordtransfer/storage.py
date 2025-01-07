from django.conf import settings
from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):
    """Overwrites files in storage if they have the same name.

    Django's default method of storing files named the same thing is to append a unique suffix to
    the file name and saving the duplicate file there. This class overrides that behviour and
    overwrites any file being saved with a path that already exists.
    """

    def _save(self, name, content):
        self.delete(name)
        return super()._save(name, content)

    def get_available_name(self, name, max_length=None):
        return name


class UploadedFileStorage(FileSystemStorage):
    """Stores files in UPLOAD_STORAGE_FOLDER."""

    def __init__(self, **kwargs):
        kwargs["location"] = settings.UPLOAD_STORAGE_FOLDER
        super().__init__(**kwargs)

    def url(self, name):
        """Generate the URL based on MEDIA_URL and the relative path."""
        relative_path = name.replace(settings.UPLOAD_STORAGE_FOLDER, "").lstrip("/")
        return f"{settings.MEDIA_URL}uploaded_files/{relative_path}"


class TempFileStorage(FileSystemStorage):
    """Stores files in TEMP_STORAGE_FOLDER."""

    def __init__(self, **kwargs):
        kwargs["location"] = settings.TEMP_STORAGE_FOLDER
        super().__init__(**kwargs)

    def url(self, name):
        """Generate the URL based on MEDIA_URL and the relative path."""
        relative_path = name.replace(settings.TEMP_STORAGE_FOLDER, "").lstrip("/")
        return f"{settings.MEDIA_URL}temp/{relative_path}"
