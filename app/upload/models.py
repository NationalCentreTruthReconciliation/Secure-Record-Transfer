from __future__ import annotations

import logging
import shutil
from itertools import chain
from pathlib import Path
from typing import Optional, Self

from django.conf import settings
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

# TODO: This module should not depend on recordtransfer!
from recordtransfer.utils import get_human_readable_file_count, get_human_readable_size

from .managers import UploadSessionManager
from .storage import TempFileStorage, UploadedFileStorage

LOGGER = logging.getLogger(__name__)

User = settings.AUTH_USER_MODEL


class UploadSession(models.Model):
    """Represents a file upload session. This model is used to track the files that a
    user uploads during a session.

    The following state diagram illustrates the possible states and transitions for an
    UploadSession:

    .. mermaid::
       :caption: UploadSession State Diagram

       flowchart TD
       CREATED --> EXPIRED
       CREATED --> UPLOADING
       UPLOADING --> CREATED
       UPLOADING --> EXPIRED
       UPLOADING --> COPYING_IN_PROGRESS
       UPLOADING --> REMOVING_IN_PROGRESS
       COPYING_IN_PROGRESS --> COPYING_FAILED
       COPYING_IN_PROGRESS --> STORED
       STORED --> COPYING_IN_PROGRESS
       STORED --> REMOVING_IN_PROGRESS
       REMOVING_IN_PROGRESS --> CREATED
    """

    class SessionStatus(models.TextChoices):
        """The status of the session."""

        CREATED = "CR", _("Session Created")
        EXPIRED = "EX", _("Session Expired")
        UPLOADING = "UG", _("Uploading Files")
        COPYING_IN_PROGRESS = "CP", _("File Copy in Progress")
        STORED = "SD", _("All Files in Permanent Storage")
        COPYING_FAILED = "FD", _("Copying Failed")
        REMOVING_IN_PROGRESS = "RP", _("File Removal in Progress")

        def __str__(self) -> str:
            """Return the string representation of the session status."""
            return self.name

    token = models.CharField(max_length=32)
    started_at = models.DateTimeField()
    status = models.CharField(
        max_length=2, choices=SessionStatus.choices, default=SessionStatus.CREATED
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    last_upload_interaction_time = models.DateTimeField(auto_now_add=True)

    objects = UploadSessionManager()

    @classmethod
    def new_session(cls, user: Optional[User] = None) -> Self:
        """Start a new upload session."""
        return cls.objects.create(
            token=get_random_string(32), started_at=timezone.now(), user=user
        )

    @property
    def upload_size(self) -> int:
        """Get total size (in bytes) of all uploaded files in this session. This includes the size
        of both temporary and permanent files.
        """
        if self.status == self.SessionStatus.EXPIRED:
            return 0
        elif self.status in (
            self.SessionStatus.COPYING_IN_PROGRESS,
            self.SessionStatus.REMOVING_IN_PROGRESS,
        ):
            raise ValueError(
                f"Cannot get upload size from session {self.token} while copying or removing "
                "files is in progress"
            )
        return sum(
            f.file_upload.size
            for f in chain(self.tempuploadedfile_set.all(), self.permuploadedfile_set.all())  # type: ignore
            if f.exists
        )

    @property
    def file_count(self) -> int:
        """Get the total count of temporary + permanent uploaded files."""
        if self.status == self.SessionStatus.EXPIRED:
            return 0
        elif self.status in (
            self.SessionStatus.COPYING_IN_PROGRESS,
            self.SessionStatus.REMOVING_IN_PROGRESS,
        ):
            raise ValueError(
                f"Cannot get file count from session {self.token} while copying or removing files "
                "is in progress"
            )
        return sum(
            f.exists
            for f in chain(self.permuploadedfile_set.all(), self.tempuploadedfile_set.all())  # type: ignore
        )

    @property
    def expires_at(self) -> Optional[timezone.datetime]:
        """Calculate this session's expiration time. Only sessions in the CREATED, UPLOADING, or
        EXPIRED state can have an expiration time. Returns None for sessions in other states, or
        if the upload session expiry feature is disabled.
        """
        if settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES == -1:
            return None

        if self.status in (
            self.SessionStatus.CREATED,
            self.SessionStatus.UPLOADING,
            self.SessionStatus.EXPIRED,
        ):
            return self.last_upload_interaction_time + timezone.timedelta(
                minutes=settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
            )
        return None

    @property
    def is_expired(self) -> bool:
        """Determine if this session has expired. A session is considered expired if it is in the
        EXPIRED state, or if it has gone past its expiration time.
        """
        expires_at = self.expires_at
        return self.status == self.SessionStatus.EXPIRED or (
            expires_at is not None and expires_at < timezone.now()
        )

    @property
    def expires_soon(self) -> bool:
        """Determine if this session will expire within the set expiration reminder time."""
        threshold = settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES
        if threshold == -1:
            return False
        return self.expires_within(minutes=threshold)

    def expires_within(self, minutes: int) -> bool:
        """Determine if this session will expire within the given number of minutes.

        Args:
            minutes: The number of minutes in the future to check for expiration.

        Returns:
            True if the session will expire before the given number of minutes from now, False
            otherwise.
        """
        expiry_time = self.expires_at
        if expiry_time is None:
            return False
        return expiry_time < timezone.now() + timezone.timedelta(minutes=minutes)

    def expire(self) -> None:
        """Set the status of this session to EXPIRED, but only if the current status is
        CREATED or UPLOADING.

        Raises:
            ValueError: If the current status is not CREATED or UPLOADING.
        """
        if self.status not in (self.SessionStatus.CREATED, self.SessionStatus.UPLOADING):
            raise ValueError(
                f"Cannot mark session {self.token} as expired because the session status "
                f"is {self.status} and not {self.SessionStatus.CREATED} or "
                f"{self.SessionStatus.UPLOADING}"
            )

        self.remove_temp_uploads(save=False)

        self.status = self.SessionStatus.EXPIRED
        self.save()

    def touch(self, save: bool = True) -> None:
        """Reset the last upload interaction time to the current time."""
        if self.status not in (self.SessionStatus.UPLOADING, self.SessionStatus.CREATED):
            return

        self.last_upload_interaction_time = timezone.now()
        if save:
            self.save()

    def add_temp_file(self, file: UploadedFile) -> TempUploadedFile:
        """Add a temporary uploaded file to this session."""
        if self.status not in (self.SessionStatus.CREATED, self.SessionStatus.UPLOADING):
            raise ValueError(
                f"Cannot add temporary uploaded file to session {self.token} because the session "
                f"status is {self.status} and not {self.SessionStatus.CREATED} or "
                f"{self.SessionStatus.UPLOADING}"
            )

        temp_file = TempUploadedFile(session=self, file_upload=file, name=file.name)
        temp_file.save()

        self.touch(save=False)

        if self.status == self.SessionStatus.CREATED:
            self.status = self.SessionStatus.UPLOADING

        self.save()

        return temp_file

    def remove_temp_file_by_name(self, name: str) -> None:
        """Remove a temporary uploaded file from this session by name."""
        if self.status != self.SessionStatus.UPLOADING:
            raise ValueError(
                f"Cannot remove temporary uploaded file from session {self.token} because the "
                f"session status is {self.status} and not {self.SessionStatus.UPLOADING}"
            )
        try:
            temp_file = self.tempuploadedfile_set.get(name=name)  # type: ignore
        except TempUploadedFile.DoesNotExist as exc:
            raise FileNotFoundError(
                f"No temporary file with name {name} exists in session {self.token}"
            ) from exc

        temp_file.delete()

        if self.file_count == 0:
            self.status = self.SessionStatus.CREATED
            self.save()

    def get_file_by_name(self, name: str) -> BaseUploadedFile:
        """Get an uploaded file in this session by name. The file can be either temporary or
        permanent.

        Args:
            name: The name of the file to find
        """
        if self.status not in (self.SessionStatus.UPLOADING, self.SessionStatus.STORED):
            raise ValueError(
                f"Can only get uploaded files from session {self.token} when the "
                f"session status is {self.SessionStatus.UPLOADING} or {self.SessionStatus.STORED}, "
            )

        try:
            if self.status == self.SessionStatus.UPLOADING:
                return self.tempuploadedfile_set.get(name=name)  # type: ignore
            else:
                return self.permuploadedfile_set.get(name=name)  # type: ignore
        except TempUploadedFile.DoesNotExist as exc:
            raise FileNotFoundError(
                f"No temporary file with name {name} exists in session {self.token}"
            ) from exc
        except PermUploadedFile.DoesNotExist as exc:
            raise FileNotFoundError(
                f"No permanent file with name {name} exists in session {self.token}"
            ) from exc

    def get_temporary_uploads(self) -> list[TempUploadedFile]:
        """Get a list of temporary uploaded files associated with this session.

        May be empty if temp uploads have already been moved to permanent storage.
        """
        if self.status in (self.SessionStatus.CREATED, self.SessionStatus.STORED):
            return []
        elif self.status == self.SessionStatus.EXPIRED:
            raise ValueError(
                f"Cannot get temporary uploaded files from session {self.token} because the "
                "session has expired."
            )
        elif self.status in (
            self.SessionStatus.COPYING_IN_PROGRESS,
            self.SessionStatus.REMOVING_IN_PROGRESS,
        ):
            raise ValueError(
                f"Cannot get temporary uploaded files from session {self.token} while copy or "
                "removal of files is in progress"
            )
        return [f for f in self.tempuploadedfile_set.all() if f.exists]  # type: ignore

    def get_permanent_uploads(self) -> list[PermUploadedFile]:
        """Get a list of permanent uploaded files associated with this session.

        May be empty if temp uploads have not been moved.
        """
        if self.status in (
            self.SessionStatus.CREATED,
            self.SessionStatus.UPLOADING,
        ):
            return []
        elif self.status == self.SessionStatus.EXPIRED:
            raise ValueError(
                f"Cannot get permanent uploaded files from session {self.token} because the "
                "session has expired."
            )
        elif self.status in (
            self.SessionStatus.COPYING_IN_PROGRESS,
            self.SessionStatus.REMOVING_IN_PROGRESS,
        ):
            raise ValueError(
                f"Cannot get permanent uploaded files from session {self.token} while copy or "
                "removal of files is in progress"
            )
        return [f for f in self.permuploadedfile_set.all() if f.exists]  # type: ignore

    def get_uploads(self) -> list[TempUploadedFile] | list[PermUploadedFile]:
        """Get a list of temporary or permanent uploaded files associated with this session. Will
        return temporary files if in the UPLOADING state, and permanent files if in the STORED
        state.
        """
        if self.status == self.SessionStatus.CREATED:
            return []
        elif self.status == self.SessionStatus.UPLOADING:
            return self.get_temporary_uploads()
        elif self.status == self.SessionStatus.STORED:
            return self.get_permanent_uploads()
        else:
            raise ValueError(
                f"Cannot get uploaded files from session {self.token} because the session status "
                f"is {self.status} and not {self.SessionStatus.UPLOADING} or "
                f"{self.SessionStatus.STORED}"
            )

    def remove_temp_uploads(self, save: bool = True) -> None:
        """Remove all temp uploaded files associated with this session."""
        if self.status == self.SessionStatus.REMOVING_IN_PROGRESS:
            LOGGER.warning("File removal is already in progress for session %s", self.token)
            return
        elif self.status == self.SessionStatus.CREATED:
            LOGGER.warning("There are no uploaded files in the session %s to remove", self.token)
            return
        elif self.status == self.SessionStatus.EXPIRED:
            raise ValueError(
                f"Cannot remove uploaded files from session {self.token} because the session has "
                "expired."
            )
        elif self.status == self.SessionStatus.COPYING_IN_PROGRESS:
            raise ValueError(
                f"Cannot remove uploaded files from session {self.token} while copying files is "
                "in progress"
            )
        elif self.status == self.SessionStatus.STORED:
            raise ValueError(
                f"Cannot remove uploaded files from session {self.token} because the files are "
                "already in permanent storage"
            )

        initial_status = self.status
        self.status = self.SessionStatus.REMOVING_IN_PROGRESS
        self.save()

        for f in self.tempuploadedfile_set.all():  # type: ignore
            f.remove()

        if initial_status == self.SessionStatus.UPLOADING:
            self.status = self.SessionStatus.CREATED
            if save:
                self.save()

    def make_uploads_permanent(self) -> None:
        """Make all temporary uploaded files associated with this session permanent."""
        if self.status == self.SessionStatus.STORED:
            LOGGER.info(
                "All uploaded files in session %s are already in permanent storage", self.token
            )
            return

        if self.status != self.SessionStatus.UPLOADING:
            raise ValueError(
                f"Cannot make uploaded files permanent in session {self.token} because session "
                f"status is {self.status} and not {self.SessionStatus.UPLOADING}"
            )

        # Set the status to indicate that the files are being copied to permanent storage
        self.status = self.SessionStatus.COPYING_IN_PROGRESS
        self.save()

        files = self.tempuploadedfile_set.all()  # type: ignore

        LOGGER.info(
            "Moving %d temporary uploaded files from the session %s to permanent storage",
            len(files),
            self.token,
        )
        try:
            for uploaded_file in files:
                uploaded_file.move_to_permanent_storage()
        except Exception as e:
            LOGGER.error(
                "An error occurred while moving uploaded files to permanent storage: %s", e
            )
            self.status = self.SessionStatus.COPYING_FAILED
            self.save()
            return
        self.status = self.SessionStatus.STORED
        self.save()

    def copy_session_uploads(self, destination: str) -> tuple[list[str], list[str]]:
        """Copy permanent uploaded files associated with this session to a destination directory.

        Args:
            destination: The destination directory

        Returns:
            A tuple containing lists of copied and missing files
        """
        if self.status == self.SessionStatus.COPYING_IN_PROGRESS:
            raise ValueError(
                f"Cannot copy files from session {self.token} to {destination} because the "
                "copying is already in progress"
            )

        if self.status != self.SessionStatus.STORED:
            raise ValueError(
                f"Cannot copy files from session {self.token} to {destination} because the"
                f"session status is {self.status} and not {self.SessionStatus.STORED}"
            )

        self.status = self.SessionStatus.COPYING_IN_PROGRESS
        self.save()

        destination_path = Path(destination)
        if not destination_path.exists():
            LOGGER.error("The destination path %s does not exist!", destination)
            raise FileNotFoundError(f"The destination path {destination} does not exist!")

        files = self.permuploadedfile_set.all()  # type: ignore

        LOGGER.info("Copying %d files to %s", len(files), destination)
        copied, missing = [], []
        for f in files:
            if not f.exists:
                LOGGER.error('File "%s" was moved or deleted', f.file_upload.path)
                missing.append(f.file_upload.path)
                continue

            if f.name is not None:
                new_path = destination_path / f.name
                LOGGER.info("Copying %s to %s", f.file_upload.path, new_path)
                f.copy(str(new_path))
                copied.append(str(new_path))
            else:
                LOGGER.error('File name is None for file "%s"', f.file_upload.path)
                missing.append(f.file_upload.path)

        # No need to set status to COPYING_FAILED even if some files are missing
        self.status = self.SessionStatus.STORED
        self.save()

        return copied, missing

    def get_quantity_and_unit_of_measure(self) -> str:
        """Create a human-readable statement of how many files are in this session.

        If the session is in the state UPLOADING, returns a count of temp files. If the session is
        in the state STORED, returns a count of permanent files. If the session is in the state
        CREATED, returns an appropriate value that indicates the lack of files.

        Uses the :ref:`ACCEPTED_FILE_FORMATS` setting to group file types together.

        Returns:
            A human readable count and size of all files in this session.
        """
        if not settings.FILE_UPLOAD_ENABLED:
            return ""

        if self.status not in (
            self.SessionStatus.CREATED,
            self.SessionStatus.UPLOADING,
            self.SessionStatus.STORED,
        ):
            raise ValueError(
                f"Cannot get quantity and unit of measure from session {self.token} because the "
                f"session status is {self.status} and not {self.SessionStatus.UPLOADING} or "
                f"{self.SessionStatus.STORED}"
            )

        size = get_human_readable_size(self.upload_size, base=1000, precision=2)

        count = get_human_readable_file_count(
            [f.name for f in self.get_uploads()], settings.ACCEPTED_FILE_FORMATS
        )

        return _("%(file_count)s, totalling %(total_size)s") % {
            "file_count": count,
            "total_size": size,
        }

    def __str__(self):
        """Return a string representation of this object."""
        token_substr = self.token[0:8] + "..." if len(self.token) > 8 else self.token

        try:
            file_count = self.file_count

            return ngettext(
                "Session %(token)s (%(count)s file, started: %(date)s)",
                "Session %(token)s (%(count)s files, started: %(date)s)",
                file_count,
            ) % {
                "token": token_substr,
                "count": file_count,
                "date": date_format(self.started_at, format="DATETIME_FORMAT", use_l10n=True),
            }

        except ValueError:
            # An exception may be thrown if the session is in an in-between state
            return _("%(token)s (started at %(date)s)") % {
                "token": token_substr,
                "date": self.started_at,
            }


def session_upload_location(instance: TempUploadedFile, filename: str) -> str:
    """Generate the upload location for a session file."""
    if instance.session:
        return "{0}/{1}".format(instance.session.token, filename)
    return "NOSESSION/{0}".format(filename)


class BaseUploadedFile(models.Model):
    """Base class for uploaded files with shared methods."""

    name = models.CharField(max_length=256, null=True, default="-")
    session = models.ForeignKey(UploadSession, on_delete=models.CASCADE, null=False)
    file_upload = models.FileField(null=True)

    class Meta:
        """Meta information for the BaseUploadedFile model."""

        abstract = True

    @property
    def exists(self) -> bool:
        """Determine if the file this object represents exists on the file system.

        Returns:
            (bool): True if file exists, False otherwise
        """
        return bool(self.file_upload) and self.file_upload.storage.exists(self.file_upload.name)

    def copy(self, new_path: str) -> None:
        """Copy this file to a new path.

        Args:
            new_path: The new path to copy this file to
        """
        if self.file_upload:
            shutil.copy2(self.file_upload.path, new_path)

    def remove(self) -> None:
        """Remove this file from the file system."""
        if self.exists:
            self.file_upload.delete()

    def get_file_media_url(self) -> str:
        """Generate the media URL to this file.

        Raises:
            FileNotFoundError if the file does not exist.
        """
        if self.exists:
            return self.file_upload.url
        raise FileNotFoundError(f"{self.name} does not exist in session {self.session.token}")

    def get_file_access_url(self) -> str:
        """Generate URL to request access for this file."""
        return reverse(
            "recordtransfer:uploaded_file",
            kwargs={
                "session_token": self.session.token,
                "file_name": self.name,
            },
        )

    def __str__(self):
        """Return a string representation of this object."""
        if self.exists:
            return f"{self.name} | {self.session}"
        return _("%(name)s Removed! | %(session)s") % {
            "name": self.name,
            "session": str(self.session),
        }


class TempUploadedFile(BaseUploadedFile):
    """Represent a temporary file that a user uploaded during an upload session."""

    class Meta(BaseUploadedFile.Meta):
        """Meta information."""

        verbose_name = "File Currently Being Uploaded"
        verbose_name_plural = "Files Currently Being Uploaded"

    file_upload = models.FileField(
        null=True, storage=TempFileStorage, upload_to=session_upload_location
    )

    def move_to_permanent_storage(self) -> None:
        """Move the file from TempFileStorage to UploadedFileStorage."""
        if self.exists:
            perm_file = PermUploadedFile(name=self.name, session=self.session)
            perm_file.file_upload.save(self.file_upload.name, File(self.file_upload.file))
            perm_file.save()
            self.delete()


class PermUploadedFile(BaseUploadedFile):
    """Represent a file that a user uploaded and has been stored."""

    class Meta(BaseUploadedFile.Meta):
        """Meta information."""

        verbose_name = "Permanent uploaded file"
        verbose_name_plural = "Permanent uploaded files"

    file_upload = models.FileField(null=True, storage=UploadedFileStorage)


@receiver(pre_delete, sender=TempUploadedFile)
@receiver(pre_delete, sender=PermUploadedFile)
def delete_file_on_model_delete(
    sender: TempUploadedFile | PermUploadedFile,
    instance: TempUploadedFile | PermUploadedFile,
    **kwargs,
) -> None:
    """Delete the actual file when an uploaded file model instance is deleted.

    Args:
        sender: The model class that sent the signal
        instance: The model uploaded file instance being deleted
        **kwargs: Additional keyword arguments passed to the signal handler
    """
    if instance.exists:
        instance.file_upload.delete()
        if isinstance(instance, TempUploadedFile):
            instance.session.touch()
