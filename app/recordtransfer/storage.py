from pathlib import Path

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


class MediaFileStorage(FileSystemStorage):
    """Base class for custom file storage."""

    def __init__(self, location: str, **kwargs):
        """Set the location of the storage. The location has to be a subdirectory of MEDIA_ROOT."""
        # Check if the location is a subdirectory of MEDIA_ROOT
        media_root = Path(settings.MEDIA_ROOT).resolve()
        location_path = Path(location).resolve()

        if not location_path.is_relative_to(media_root):
            raise ValueError("The location must be a subdirectory of MEDIA_ROOT")

        relative_path = location_path.relative_to(media_root)

        base_url = Path(settings.MEDIA_URL / relative_path).as_posix()
        kwargs["base_url"] = base_url
        kwargs["location"] = str(location)
        super().__init__(**kwargs)

    def url(self, name: str) -> str:
        """Generate the URL based on MEDIA_URL and the relative path."""
        return (Path(self.base_url) / name).as_posix()


class UploadedFileStorage(MediaFileStorage):
    """Stores files in UPLOAD_STORAGE_FOLDER."""

    def __init__(self, **kwargs):
        super().__init__(settings.UPLOAD_STORAGE_FOLDER, **kwargs)


class TempFileStorage(MediaFileStorage):
    """Stores files in TEMP_STORAGE_FOLDER."""

    def __init__(self, **kwargs):
        super().__init__(settings.TEMP_STORAGE_FOLDER, **kwargs)
