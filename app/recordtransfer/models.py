from __future__ import annotations

import logging
import os
import shutil
import uuid
from itertools import chain
from pathlib import Path
from typing import ClassVar, Optional, Union

import bagit
from caais.export import ExportVersion
from caais.models import Metadata
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from recordtransfer.enums import SubmissionStep
from recordtransfer.managers import (
    InProgressSubmissionManager,
    SubmissionQuerySet,
    UploadSessionManager,
)
from recordtransfer.storage import OverwriteStorage, TempFileStorage, UploadedFileStorage
from recordtransfer.utils import get_human_readable_file_count, get_human_readable_size

LOGGER = logging.getLogger("recordtransfer")


class User(AbstractUser):
    """The main User object used to authenticate users"""

    gets_submission_email_updates = models.BooleanField(default=False)
    confirmed_email = models.BooleanField(default=False)
    gets_notification_emails = models.BooleanField(default=True)

    def get_full_name(self):
        return self.first_name + " " + self.last_name


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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    last_upload_interaction_time = models.DateTimeField(auto_now_add=True)

    objects = UploadSessionManager()

    @classmethod
    def new_session(cls, user: Optional[User] = None) -> UploadSession:
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
            for f in chain(self.tempuploadedfile_set.all(), self.permuploadedfile_set.all())
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
            for f in chain(self.permuploadedfile_set.all(), self.tempuploadedfile_set.all())
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
            temp_file = self.tempuploadedfile_set.get(name=name)
        except TempUploadedFile.DoesNotExist as exc:
            raise FileNotFoundError(
                f"No temporary file with name {name} exists in session {self.token}"
            ) from exc

        temp_file.delete()

        if self.file_count == 0:
            self.status = self.SessionStatus.CREATED
            self.save()

    def get_temp_file_by_name(self, name: str) -> TempUploadedFile:
        """Get an temporary uploaded file in this session by name.

        Args:
            name: The name of the file to find
        """
        if self.status != self.SessionStatus.UPLOADING:
            raise ValueError(
                f"Can only get temporary uploaded files from session {self.token} when the "
                f"session status is {self.SessionStatus.UPLOADING}"
            )

        try:
            return self.tempuploadedfile_set.get(name=name)
        except TempUploadedFile.DoesNotExist as exc:
            raise FileNotFoundError(
                f"No temporary file with name {name} exists in session {self.token}"
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
        return [f for f in self.tempuploadedfile_set.all() if f.exists]

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
        return [f for f in self.permuploadedfile_set.all() if f.exists]

    def get_uploads(self) -> Union[list[TempUploadedFile], list[PermUploadedFile]]:
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

        for f in self.tempuploadedfile_set.all():
            f.remove()

        if initial_status == self.SessionStatus.UPLOADING:
            self.status = self.SessionStatus.CREATED
            if save:
                self.save()

    def make_uploads_permanent(self, logger: Optional[logging.Logger] = None) -> None:
        """Make all temporary uploaded files associated with this session permanent.

        Args:
            logger: Optional logger instance to use for logging operations
        """
        logger = logger or LOGGER

        if self.status == self.SessionStatus.STORED:
            logger.info(
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

        files = self.tempuploadedfile_set.all()

        logger.info(
            "Moving %d temporary uploaded files from the session %s to permanent storage",
            len(files),
            self.token,
        )
        try:
            for uploaded_file in files:
                uploaded_file.move_to_permanent_storage()
        except Exception as e:
            logger.error(
                "An error occurred while moving uploaded files to permanent storage: %s", e
            )
            self.status = self.SessionStatus.COPYING_FAILED
            self.save()
            return
        self.status = self.SessionStatus.STORED
        self.save()

    def copy_session_uploads(
        self, destination: str, logger: Optional[logging.Logger] = None
    ) -> tuple[list[str], list[str]]:
        """Copy permanent uploaded files associated with this session to a destination directory.

        Args:
            destination: The destination directory
            logger: A logger object

        Returns:
            A tuple containing lists of copied and missing files
        """
        logger = logger or LOGGER

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
            logger.error("The destination path %s does not exist!", destination)
            raise FileNotFoundError(f"The destination path {destination} does not exist!")

        files = self.permuploadedfile_set.all()

        logger.info("Copying %d files to %s", len(files), destination)
        copied, missing = [], []
        for f in files:
            if not f.exists:
                logger.error('File "%s" was moved or deleted', f.file_upload.path)
                missing.append(f.file_upload.path)
                continue

            if f.name is not None:
                new_path = destination_path / f.name
                logger.info("Copying %s to %s", f.file_upload.path, new_path)
                f.copy(str(new_path))
                copied.append(str(new_path))
            else:
                logger.error('File name is None for file "%s"', f.file_upload.path)
                missing.append(f.file_upload.path)

        # No need to set status to COPYING_FAILED even if some files are missing
        self.status = self.SessionStatus.STORED
        self.save()

        return copied, missing

    def get_quantity_and_unit_of_measure(self) -> str:
        """Create a human-readable statement of how many files are in this session.

        If the session is in the state UPLOADING, returns a count of temp files. If the session is
        in the state STORED, returns a count of permanent files. If the session is in the state CREATED,
        returns an appropriate value that indicates the lack of files.

        Uses the :ref:`ACCEPTED_FILE_FORMATS` setting to group file types together.

        Returns:
            A human readable count and size of all files in this session.
        """
        if not settings.FILE_UPLOAD_ENABLED:
            return

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
            [f.name for f in self.get_uploads()],
            settings.ACCEPTED_FILE_FORMATS,
            LOGGER,
        )

        return _("{0}, totalling {1}").format(count, size)

    def __str__(self):
        """Return a string representation of this object."""
        return f"{self.token} ({self.started_at}) | {self.status}"


def session_upload_location(instance, filename: str) -> str:
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
            return f"{self.name} | Session {self.session}"
        return f"{self.name} Removed! | Session {self.session}"


class TempUploadedFile(BaseUploadedFile):
    """Represent a temporary file that a user uploaded during an upload session."""

    class Meta(BaseUploadedFile.Meta):
        """Meta information."""

        verbose_name = "Temporary uploaded file"
        verbose_name_plural = "Temporary uploaded files"

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
    sender: Union[TempUploadedFile, PermUploadedFile],
    instance: Union[TempUploadedFile, PermUploadedFile],
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


class SubmissionGroup(models.Model):
    """Represents a group of submissions.

    Attributes:
        name (CharField):
            The name of the group
        description (TextField):
            A description of the group
        created_by (ForeignKey):
            The user who created the group
        uuid (UUIDField):
            A unique ID for the group
    """

    name = models.CharField(max_length=256, null=False)
    description = models.TextField(default="")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    uuid = models.UUIDField(default=uuid.uuid4)

    @property
    def number_of_submissions_in_group(self):
        return len(self.submission_set.all())

    def get_absolute_url(self) -> str:
        """Return the URL to access a detail view of this submission group."""
        return reverse("recordtransfer:submission_group_detail", kwargs={"uuid": self.uuid})

    def __str__(self):
        return f"{self.name} ({self.created_by})"


class Submission(models.Model):
    """The object that represents a user's submission, including metadata, and
    the files they submitted.

    Attributes:
        submission_date (DateTimeField):
            The date and time the submission was made
        user (User):
            The user who submitted the metadata (and optionally, files)
        raw_form (BinaryField):
            A pickled object containing the transfer form as it was submitted
        metadata (OneToOneField):
            Foreign key to a :py:class:`~caais.models.Metadata` object. The
            metadata object is generated from the form metadata, and any
            defaults that have been set in the settings
        part_of_group (ForeignKey):
            The group that this submission is a part of
        upload_session (UploadSession):
            The upload session associated with this submission. If file uploads
            are disabled, this will always be NULL/None
        uuid (UUIDField):
            A unique ID for the submission
        bag_name (str):
            A name that is used when the Submission is to be dumped to the file
            system as a BagIt bag
    """

    submission_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    raw_form = models.BinaryField(
        default=b"", null=True
    )  # A raw capture of the form before submission
    metadata = models.OneToOneField(
        Metadata, on_delete=models.CASCADE, null=True, related_name="submission"
    )
    part_of_group = models.ForeignKey(
        SubmissionGroup, on_delete=models.SET_NULL, blank=True, null=True
    )
    upload_session = models.ForeignKey(UploadSession, null=True, on_delete=models.SET_NULL)
    uuid = models.UUIDField(default=uuid.uuid4)
    bag_name = models.CharField(max_length=256, null=True)

    objects = SubmissionQuerySet.as_manager()

    def generate_bag_name(self) -> None:
        """Generate a name suitable for a submission bag, and set self.bag_name to that name.

        Raises:
            ValueError: If there is no metadata or no user associated with this submission.
        """
        if self.bag_name:
            return

        if not self.metadata:
            raise ValueError(
                "There is no metadata associated with this submission, cannot generate a bag name"
            )
        if not self.user:
            raise ValueError("There is no user associated with this submission")

        title = self.metadata.accession_title or "No title"
        abbrev_title = title if len(title) <= 20 else title[0:20]

        bag_name = "{username}_{datetime}_{title}".format(
            username=slugify(self.user.username),
            datetime=timezone.localtime(timezone.now()).strftime(r"%Y%m%d-%H%M%S"),
            title=slugify(abbrev_title),
        )

        self.bag_name = bag_name
        self.save()

    @property
    def user_folder(self) -> str:
        """Get the location of the submission user's bag storage folder.

        Raises:
            FileNotFoundError: If BAG_STORAGE_FOLDER is not set.
            ValueError: If there is no user associated with this submission.
        """
        if not settings.BAG_STORAGE_FOLDER:
            raise FileNotFoundError("BAG_STORAGE_FOLDER is not set")
        if not self.user:
            raise ValueError("There is no user associated with this submission")
        return os.path.join(str(settings.BAG_STORAGE_FOLDER), slugify(self.user.username))

    @property
    def location(self) -> str:
        """Get the location on the file system for the BagIt bag for this submission.

        Raises:
            ValueError: If there is no user associated with this submission.
        """
        if not self.user:
            raise ValueError("There is no user associated with this submission")
        if not self.bag_name:
            self.generate_bag_name()
        return os.path.join(self.user_folder, self.bag_name)  # type: ignore

    @property
    def extent_statements(self):
        """Return the first extent statement for this submission."""
        return (
            next(
                (e.quantity_and_unit_of_measure for e in self.metadata.extent_statements.all()), ""
            )
            if self.metadata
            else ""
        )

    def get_admin_metadata_change_url(self):
        """Get the URL to change the metadata object in the admin"""
        view_name = "admin:{0}_{1}_change".format(
            self.metadata._meta.app_label, self.metadata._meta.model_name
        )
        return reverse(view_name, args=(self.metadata.pk,))

    def get_admin_metadata_change_url(self):
        """Get the URL to change the metadata object in the admin"""
        view_name = "admin:{0}_{1}_change".format(
            self.metadata._meta.app_label, self.metadata._meta.model_name
        )
        return reverse(view_name, args=(self.metadata.pk,))

    def get_admin_change_url(self):
        """Get the URL to change this object in the admin"""
        view_name = "admin:{0}_{1}_change".format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def get_admin_report_url(self):
        """Get the URL to generate a report for this object in the admin"""
        view_name = "admin:{0}_{1}_report".format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def get_admin_zip_url(self):
        """Get the URL to generate a zipped bag for this object in the admin"""
        view_name = f"admin:{self._meta.app_label}_{self._meta.model_name}_zip"
        return reverse(view_name, args=(self.pk,))

    def __str__(self):
        return f"Submission by {self.user} at {self.submission_date}"

    def make_bag(
        self,
        algorithms: Union[str, list] = "sha512",
        file_perms: str = "644",
        logger: Optional[logging.Logger] = None,
    ):
        """Create a BagIt bag on the file system for this Submission. The location of the BagIt bag
        is determined by self.location. Checks the validity of the Bag post-creation to ensure that
        integrity is maintained. The data payload files come from the UploadSession associated with
        this submission.

        Args:
            algorithms (Union[str, list]): The algorithms to generate the BagIt bag with
            file_perms (str): A string-based octal "chmod" number
            logger: A logger instance (optional)
        """
        logger = logger or LOGGER

        if not algorithms:
            raise ValueError("algorithms cannot be empty")

        if not self.upload_session:
            raise ValueError("This submission has no associated upload session")

        if not self.metadata:
            raise ValueError("This submission has no associated metadata")

        if isinstance(algorithms, str):
            algorithms = [a.strip() for a in algorithms.split(",")]

        for algorithm in algorithms:
            if algorithm not in bagit.CHECKSUM_ALGOS:
                raise ValueError("{0} is not a valid checksum algorithm".format(algorithm))

        if not os.path.exists(settings.BAG_STORAGE_FOLDER) or not os.path.isdir(
            settings.BAG_STORAGE_FOLDER
        ):
            LOGGER.error(
                'The BAG_STORAGE_FOLDER "%s" does not exist!', settings.BAG_STORAGE_FOLDER
            )
            return {
                "missing_files": [],
                "bag_created": False,
                "bag_valid": False,
                "time_created": None,
            }

        if not os.path.exists(self.user_folder) or not os.path.isdir(self.user_folder):
            os.mkdir(self.user_folder)
            LOGGER.info('Created new user folder at "%s"', self.user_folder)

        if os.path.exists(self.location):
            LOGGER.warning('A bag already exists at "%s"', self.location)
            return {
                "missing_files": [],
                "bag_created": False,
                "bag_valid": False,
                "time_created": None,
            }

        os.mkdir(self.location)
        LOGGER.info('Created new bag folder at "%s"', self.user_folder)

        copied, missing = self.upload_session.copy_session_uploads(self.location, logger)

        if missing:
            LOGGER.error("One or more uploaded files is missing!")
            LOGGER.info('Removing bag at "%s" due to missing files', self.location)
            self.remove_bag()
            return {
                "missing_files": missing,
                "bag_created": False,
                "bag_valid": False,
                "time_created": None,
            }

        logger.info('Creating BagIt bag at "%s"', self.location)
        logger.info("Using these checksum algorithm(s): %s", ", ".join(algorithms))

        bagit_info = self.metadata.create_flat_representation(version=ExportVersion.CAAIS_1_0)
        bag = bagit.make_bag(self.location, bagit_info, checksums=algorithms)

        logger.info("Setting file mode for bag payload files to %s", file_perms)
        perms = int(file_perms, 8)
        for payload_file in bag.payload_files():
            payload_file_path = os.path.join(self.location, payload_file)
            os.chmod(payload_file_path, perms)

        logger.info('Validating the bag created at "%s"', self.location)
        valid = bag.is_valid()

        if not valid:
            logger.error("Bag is INVALID!")
            logger.info('Removing bag at "%s" since it\'s invalid', self.location)
            self.remove_bag()
            return {
                "missing_files": [],
                "bag_created": False,
                "bag_valid": False,
                "time_created": None,
            }

        logger.info("Bag is VALID")
        current_time = timezone.now()

        return {
            "missing_files": [],
            "bag_created": True,
            "bag_valid": True,
            "time_created": current_time,
        }

    def remove_bag(self):
        """Remove the BagIt bag if it exists."""
        if os.path.exists(self.location):
            shutil.rmtree(self.location)


class Job(models.Model):
    """A background job executed by an admin user."""

    class JobStatus(models.TextChoices):
        """The status of the bag's review."""

        NOT_STARTED = "NS", _("Not Started")
        IN_PROGRESS = "IP", _("In Progress")
        COMPLETE = "CP", _("Complete")
        FAILED = "FD", _("Failed")

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    name = models.CharField(max_length=256, null=True)
    description = models.TextField(null=True)
    user_triggered = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    job_status = models.CharField(
        max_length=2, choices=JobStatus.choices, default=JobStatus.NOT_STARTED
    )
    attached_file = models.FileField(
        upload_to="jobs/attachments", storage=OverwriteStorage, blank=True, null=True
    )
    message_log = models.TextField(null=True)

    def get_admin_change_url(self) -> str:
        """Get the URL to change this object in the admin."""
        view_name = "admin:{0}_{1}_change".format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def get_admin_download_url(self) -> str:
        """Get the URL to download the attached file from the admin."""
        view_name = "admin:{0}_{1}_download".format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def __str__(self) -> str:
        """Return a string representation of this object."""
        return f"{self.name} (Created by {self.user_triggered})"


class InProgressSubmission(models.Model):
    """A submission that is in progress, created when a user saves a submission form.

    Attributes:
        uuid:
            A unique ID for the submission
        user:
            The user who is submitting the form
        last_updated:
            The last time the form was updated
        current_step:
            The current step the user is on
        step_data:
            The data contained in the form
        title:
            The accession title of the submission
    """

    STEP_CHOICES: ClassVar = [(step.value, step.name) for step in SubmissionStep]

    uuid = models.UUIDField(default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_updated = models.DateTimeField(auto_now_add=True)
    current_step = models.CharField(
        max_length=20,
        choices=STEP_CHOICES,
        null=False,
        help_text="Current step in the transfer wizard process",
    )
    step_data = models.BinaryField(default=b"")
    title = models.CharField(max_length=256, null=True)
    upload_session = models.OneToOneField(
        UploadSession, null=True, on_delete=models.SET_NULL, related_name="in_progress_submission"
    )
    reminder_email_sent = models.BooleanField(default=False)

    objects = InProgressSubmissionManager()

    def clean(self) -> None:
        """Validate the current step value. This gets called when the model instance is
        modified through a form.
        """
        try:
            SubmissionStep(self.current_step)
        except ValueError:
            raise ValidationError({"current_step": ["Invalid step value"]}) from None

    @property
    def upload_session_expires_at(self) -> Optional[timezone.datetime]:
        """Get the expiration time of the upload session associated with this submission."""
        if self.upload_session:
            return self.upload_session.expires_at
        return None

    @property
    def upload_session_expired(self) -> bool:
        """Determine if the associated upload session has expired or not."""
        return self.upload_session is not None and self.upload_session.is_expired

    @property
    def upload_session_expires_soon(self) -> bool:
        """Determine if the associated upload session is expiring soon or not."""
        return self.upload_session is not None and self.upload_session.expires_soon

    def get_resume_url(self) -> str:
        """Get the URL to access and resume the in-progress submission."""
        return reverse("recordtransfer:resume_submit", kwargs={"resume": self.uuid})

    def reset_reminder_email_sent(self) -> None:
        """Reset the reminder email flag to False, if it isn't already False."""
        if self.reminder_email_sent:
            self.reminder_email_sent = False
            self.save()

    def __str__(self):
        """Return a string representation of this object."""
        title = self.title or "None"
        session = self.upload_session.token if self.upload_session else "None"
        return f"In-Progress Submission by {self.user} (Title: {title} | Session: {session})"


@receiver(pre_save, sender=InProgressSubmission)
def update_upon_save(
    sender: InProgressSubmission, instance: InProgressSubmission, **kwargs
) -> None:
    """Update the last upload interaction time of the associated upload session when the
    InProgressSubmission is saved, and reset the reminder email flag, if an upload session exists.
    """
    if instance.upload_session:
        instance.upload_session.touch()
        instance.reset_reminder_email_sent()
