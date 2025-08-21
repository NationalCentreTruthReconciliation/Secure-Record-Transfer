from pathlib import Path
from typing import Optional

from django.core.files.base import File
from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):
    """Overwrites files in storage if they have the same name.

    Django's default method of storing files named the same thing is to append a unique suffix to
    the file name and saving the duplicate file there. This class overrides that behviour and
    overwrites any file being saved with a path that already exists.
    """

    def _save(self, name: str, content: File) -> str:
        self.delete(name)
        return super()._save(name, content)

    def get_available_name(self, name: str, max_length: Optional[int] = None) -> str:
        """Return the provided file name as the available name,
        allowing overwriting of existing files.
        """
        return name

