from __future__ import annotations

import logging
import os
import shutil
import uuid
from itertools import chain
from pathlib import Path
from typing import ClassVar, Iterable, Optional, Union

import bagit
from caais.export import ExportVersion
from caais.models import Metadata
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from recordtransfer.enums import SiteSettingKey, SiteSettingType, SubmissionStep
from recordtransfer.managers import (
    InProgressSubmissionManager,
    SubmissionQuerySet,
    UploadSessionManager,
)
from recordtransfer.storage import OverwriteStorage, TempFileStorage, UploadedFileStorage
from recordtransfer.utils import get_human_readable_file_count, get_human_readable_size

LOGGER = logging.getLogger(__name__)

# Sentinel object to distinguish between cache miss and cached None values
NOT_CACHED = object()


class User(AbstractUser):
    """The main User object used to authenticate users."""

    gets_submission_email_updates = models.BooleanField(default=False)
    gets_notification_emails = models.BooleanField(default=True)
    phone_number = models.CharField(
        max_length=20,
        blank=False,
        null=True,
        help_text=_("Phone number in format: +1 (999) 999-9999"),
    )
    address_line_1 = models.CharField(
        max_length=100,
        blank=False,
        null=True,
        help_text=_("Street and street number"),
    )
    address_line_2 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Unit number, RPO, PO BOX (optional)"),
    )
    city = models.CharField(
        max_length=100,
        blank=False,
        null=True,
        help_text=_("City"),
    )
    province_or_state = models.CharField(
        max_length=64,
        blank=False,
        null=True,
        help_text=_("Province or state"),
    )
    other_province_or_state = models.CharField(
        max_length=64,
        blank=False,
        null=True,
        help_text=_("Other province or state if not listed"),
    )
    postal_or_zip_code = models.CharField(
        max_length=20,
        blank=False,
        null=True,
        help_text=_("Postal code (Canada) or zip code (US)"),
    )
    country = models.CharField(
        max_length=2,
        blank=False,
        null=True,
        help_text=_("Country code"),
    )

    @property
    def full_name(self) -> str:
        """Return the full name of the user, which is a combination of first and last names."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def has_contact_info(self) -> bool:
        """Check if user has complete contact information."""
        required_fields = [
            self.phone_number,
            self.address_line_1,
            self.city,
            self.province_or_state,
            self.postal_or_zip_code,
            self.country,
        ]

        # Check if all required fields have values
        if not all(field for field in required_fields):
            return False

        # If "Other" is selected for province/state, check if other_province_or_state is filled
        if self.province_or_state and self.province_or_state.lower() == "other":
            return bool(self.other_province_or_state)

        return True


class SiteSetting(models.Model):
    """A model to store configurable site settings that administrators can modify
    through the Django admin interface without requiring code changes.

    This model supports caching of settings values for improved performance.

    Adding a New Setting
    --------------------

    To add a new setting to the database, follow these steps:

    1. **Add a new entry to the SiteSettingKey enum class**:

       Add your new setting key to the :class:`~recordtransfer.models.SiteSetting` enum in
       `recordtransfer/enums.py`.
       The key should be descriptive and follow existing naming conventions
       (i.e., all uppercase with underscores). Include a
       :class:`~recordtransfer.enums.SettingKeyMeta` with the value type, description, and optional
       default value.

       Example::

           NEW_SETTING_NAME = SettingKeyMeta(
               SiteSettingType.STR,
               _("Description of what this setting controls."),
               default_value="Default string value",
           )

    2. **Create a data migration**:

       Create a Django data migration to add the setting to the database. The migration
       should create a new :class:`~recordtransfer.models.SiteSetting` instance with the required
       fields:

       - ``key``: Must be unique and match the enum name (string)
       - ``value``: The default value as a string (must use the enum's default_value if available)
       - ``value_type``: Either "int" for integers or "str" for strings

       Example migration for a string setting::

           from django.db import migrations


           def add_new_setting(apps, schema_editor):
               SiteSetting = apps.get_model("recordtransfer", "SiteSetting")
               SiteSetting.objects.get_or_create(
                   key="NEW_SETTING_NAME",
                   defaults={"value": "Default string value", "value_type": "str"},
               )


           class Migration(migrations.Migration):
               dependencies = [
                   ("recordtransfer", "XXXX_previous_migration"),
               ]

               operations = [
                   migrations.RunPython(add_new_setting),
               ]

    3. **Validation requirements**:

       - The ``key`` field must be unique across all settings
       - For ``value_type`` "int": the ``value`` must be a valid string representation
         of an integer (e.g., "42", "-1", "0")
       - For ``value_type`` "str": the ``value`` can be any string
       - ``change_date`` is auto-generated and ``changed_by`` does not need to be set

    4. **Document the new setting**:

       Add an entry for the new setting to ``docs/admin_guide/site_settings.rst``.

    Removing a Setting
    ------------------

    To remove an existing setting from the database:

    1. **Remove the key from the SiteSettingKey enum class**:

       Delete the corresponding enum entry from the :class:`~recordtransfer.models.SiteSetting`
       enum in `enums.py`.

    2. **Create a data migration**:

       Create a Django data migration to remove the setting from the database::

           from django.db import migrations


           def remove_old_setting(apps, schema_editor):
               SiteSetting = apps.get_model("recordtransfer", "SiteSetting")
               SiteSetting.objects.filter(key="OLD_SETTING_NAME").delete()


           class Migration(migrations.Migration):
               dependencies = [
                   ("recordtransfer", "XXXX_previous_migration"),
               ]

               operations = [
                   migrations.RunPython(remove_old_setting),
               ]

    3. **Update code references**:

       Remove any code that references the old setting key.

    4. **Update documentation**:

       Remove the setting from ``docs/admin_guide/site_settings.rst``.

    Retrieving Settings in Code
    ---------------------------

    Once a setting has been added to the database, retrieve it using the appropriate static method:

    - **For string settings**::

        value = SiteSetting.get_value_str(SiteSettingKey.SETTING_NAME)

    - **For integer settings**::

        value = SiteSetting.get_value_int(SiteSettingKey.SETTING_NAME)
    """

    key = models.CharField(
        verbose_name=_("Setting Key"), max_length=255, unique=True, null=False, editable=False
    )
    value = models.TextField(
        verbose_name=_("Setting Value"),
        blank=False,
        null=True,
    )
    value_type = models.CharField(
        max_length=8,
        choices=SiteSettingType.choices,
        default=SiteSettingType.STR,
        verbose_name=_("Setting value type"),
        null=False,
        editable=False,
    )

    change_date = models.DateTimeField(
        auto_now=True, editable=False, verbose_name=_("Change date")
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        editable=False,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Changed by"),
    )

    def set_cache(self, value: Optional[Union[str, int]]) -> None:
        """Cache the value of this setting."""
        cache.set(self.key, value)

    @staticmethod
    def get_value_str(key: SiteSettingKey) -> Optional[str]:
        """Get the value of a site setting of type :attr:`SettingType.STR` by its key.

        Args:
            key: The key of the setting to retrieve.

        Returns:
            The value of the setting as a string, cached if available, or fetched from the
            database.

        Raises:
            ValidationError: If the setting is not of type :attr:`SettingType.STR`.
        """
        val = cache.get(key.name, default=NOT_CACHED)
        if val is not NOT_CACHED:
            return val
        obj = SiteSetting.objects.get(key=key.name)

        if obj.value_type != SiteSettingType.STR:
            raise ValidationError(
                f"Setting {key.name} is not of type STR, but of type {obj.value_type}"
            )

        obj.set_cache(obj.value)
        return obj.value

    @staticmethod
    def get_value_int(key: SiteSettingKey) -> Optional[int]:
        """Get the value of a site setting of type :attr:`SettingType.INT` by its key.

        Args:
            key: The key of the setting to retrieve.

        Returns:
            The value of the setting as an integer, cached if available, or fetched from the
            database.

        Raises:
            ValidationError: If the setting is not of type :attr:`SettingType.INT`.
        """
        val = cache.get(key.name, default=NOT_CACHED)
        if val is not NOT_CACHED:
            return val

        obj = SiteSetting.objects.get(key=key.name)

        if obj.value_type != SiteSettingType.INT:
            raise ValidationError(
                f"Setting {key.name} is not of type INT, but of type {obj.value_type}"
            )

        return_value = None if obj.value is None else int(obj.value)

        obj.set_cache(return_value)
        return return_value

    def reset_to_default(self, user: Optional[User] = None) -> None:
        """Reset this setting to its default value as defined in the
        :py:class:`~recordtransfer.enums.SiteSettingKey` enum.

        Args:
            user: The user who initiated the reset operation (optional).
        """
        try:
            default_value = SiteSettingKey[self.key].default_value
        except KeyError as exc:
            raise ValueError(f"{self.key} is not a valid SiteSettingKey") from exc

        self.value = default_value
        self.change_date = timezone.now()
        if user:
            self.changed_by = user
        self.save()

    @property
    def default_value(self) -> Optional[str]:
        """Get the default value for this setting, if available. The default value is defined in
        the :class:`~recordtransfer.enums.SiteSettingKey` enum, in the form of a string.
        """
        try:
            return SiteSettingKey[self.key].default_value
        except KeyError as exc:
            raise ValueError(f"{self.key} is not a valid SiteSettingKey") from exc

    def __str__(self) -> str:
        """Return a human-readable representation of the setting."""
        try:
            return f"{self.key.replace('_', ' ').title()}"
        except ValueError:
            return f"Setting: {self.key}"


@receiver(post_save, sender=SiteSetting)
def update_cache_post_save(
    sender: SiteSetting, instance: SiteSetting, created: bool, **kwargs
) -> None:
    """Update cached value when setting is saved, but not on creation."""
    if created:
        return

    value = instance.value
    if instance.value_type == SiteSettingType.INT:
        try:
            if value is not None:
                value = int(value)
        except ValueError as exc:
            raise ValidationError(
                f"Value for setting {instance.key} must be an integer, but got '{instance.value}'"
            ) from exc
    instance.set_cache(value)


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

    def get_file_by_name(self, name: str) -> UploadedFile:
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
                return self.tempuploadedfile_set.get(name=name)
            else:
                return self.permuploadedfile_set.get(name=name)
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

        files = self.tempuploadedfile_set.all()

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

        files = self.permuploadedfile_set.all()

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
            [f.name for f in self.get_uploads()], settings.ACCEPTED_FILE_FORMATS
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

    def get_delete_url(self) -> str:
        """Return the URL to delete this submission group."""
        return reverse("recordtransfer:delete_submission_group_modal", kwargs={"uuid": self.uuid})

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

    objects = SubmissionQuerySet.as_manager()

    @property
    def bag_name(self) -> str:
        """Get a name suitable for a submission bag.

        The bag name contains the username, the date this submission was made, and the title of the
        metadata. This file name is properly sanitized to be used as a directory or part of a file
        name.

        Raises:
            ValueError: If there is no metadata or no user associated with this submission.
        """
        if not self.metadata:
            raise ValueError(
                "There is no metadata associated with this submission, cannot generate a bag name"
            )
        if not self.user:
            raise ValueError("There is no user associated with this submission")

        title = self.metadata.accession_title or "No title"
        abbrev_title = title if len(title) <= 20 else title[0:20]

        return "{username}_{datetime}_{title}".format(
            username=slugify(self.user.username),
            datetime=self.submission_date.strftime(r"%Y%m%d-%H%M%S"),
            title=slugify(abbrev_title),
        )

    @property
    def extent_statements(self) -> str:
        """Return the first extent statement for this submission."""
        return (
            next(
                (e.quantity_and_unit_of_measure for e in self.metadata.extent_statements.all()), ""
            )
            if self.metadata
            else ""
        )

    def get_admin_metadata_change_url(self) -> str:
        """Get the URL to change the metadata object in the admin."""
        if not self.metadata:
            raise ValueError("Cannot create a URL for non-existent metadata")
        view_name = "admin:{0}_{1}_change".format(
            self.metadata._meta.app_label, self.metadata._meta.model_name
        )
        return reverse(view_name, args=(self.metadata.pk,))

    def get_admin_change_url(self) -> str:
        """Get the URL to change this object in the admin."""
        view_name = "admin:{0}_{1}_change".format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def get_admin_report_url(self) -> str:
        """Get the URL to generate a report for this object in the admin."""
        view_name = "admin:{0}_{1}_report".format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def get_admin_zip_url(self) -> str:
        """Get the URL to generate a zipped bag for this object in the admin."""
        view_name = f"admin:{self._meta.app_label}_{self._meta.model_name}_zip"
        return reverse(view_name, args=(self.pk,))

    def make_bag(
        self,
        location: Path,
        algorithms: Iterable[str] = ("sha512",),
        file_perms: str = "644",
    ) -> bagit.Bag:
        """Create a BagIt bag on the file system for this Submission. Checks the validity of the
        Bag post-creation to ensure that integrity is maintained. The data payload files come from
        the UploadSession associated with this submission.

        If given a location to an existing Bag, this function will check whether the Bag can be
        updated in-place. If not, the Bag will be completely re-generated again.

        Raises:
            ValueError: If any required state is incorrect (e.g., no upload session)
            FileNotFoundError: If any files are missing when copying to temp location
            FileExistsError: If the Bag at self.location already exists
            bagit.BagValidationError: If the Bag is created, but it's invalid

        Args:
            location (Path): The path to make the Bag at
            algorithms (Iterable[str]): The checksum algorithms to generate the BagIt bag with
            file_perms (str): A string-based octal "chmod" number
        """
        if not self.metadata:
            raise ValueError(
                "This submission has no associated metadata, this is required to make a bag"
            )
        if not self.upload_session:
            raise ValueError(
                "This submission has no associated upload session, this is required to make a bag"
            )

        if location.exists() and (location / "data").exists():
            LOGGER.info('Bag already exists. Updating it in-place at "%s"', location)
            bag = self._update_existing_bag(location, algorithms, file_perms)
        else:
            LOGGER.info('Bag does not exist, creating a new one at "%s"', location)
            bag = self._create_new_bag(location, algorithms, file_perms)

        LOGGER.info('Validating the bag at "%s"', location)
        valid = bag.is_valid()

        if not valid:
            LOGGER.error("Bag is INVALID!")
            LOGGER.info('Removing bag at "%s" since it\'s invalid', location)
            self.remove_bag(location)
            raise bagit.BagValidationError("Bag was invalid!")

        LOGGER.info("Bag is VALID")
        return bag

    def _update_existing_bag(
        self,
        location: Path,
        algorithms: Iterable[str],
        file_perms: str = "644",
    ) -> bagit.Bag:
        """Update the Bag if it exists.

        If there are any files missing or any extra files, the Bag is re-generated.
        """
        assert self.upload_session, "This submission has no upload session!"
        assert self.metadata, "This submission has no associated metadata!"

        bag = None

        try:
            bag = bagit.Bag(str(location))
        except bagit.BagError as exc:
            LOGGER.warning("Encountered BagError for existing location. Error was: '%s'", exc)
            LOGGER.info("Re-generating Bag due to error")
            return self._create_new_bag(location, algorithms, file_perms)

        if set(bag.algorithms) != set(algorithms):
            LOGGER.info(
                "Checksum algorithms differ (current=%s, desired=%s), re-generating Bag",
                ",".join(bag.algorithms),
                ",".join(algorithms),
            )
            return self._create_new_bag(location, algorithms, file_perms)

        payload_file_set = {Path(payload_file).name for payload_file in bag.payload_files()}
        perm_file_set = {file.name for file in self.upload_session.get_permanent_uploads()}

        files_not_in_payload = perm_file_set - payload_file_set
        files_not_in_uploads = payload_file_set - perm_file_set

        if files_not_in_uploads or files_not_in_payload:
            if files_not_in_uploads:
                LOGGER.warning(
                    "Found %d extra file(s) in Bag not in the Upload session!",
                    len(files_not_in_uploads),
                )
            if files_not_in_payload:
                LOGGER.warning(
                    "Found %d extra file(s) in Upload session not in the Bag!",
                    len(files_not_in_payload),
                )
            LOGGER.warning("Re-generating Bag due to file count mismatch")
            return self._create_new_bag(location, algorithms, file_perms)

        # Update metadata since no files or algorithms changed, but the metadata model might have
        bagit_info = self.metadata.create_flat_representation(version=ExportVersion.CAAIS_1_0)
        bag.info.update(bagit_info)
        bag.save()

        return bag

    def _create_new_bag(
        self,
        location: Path,
        algorithms: Iterable[str],
        file_perms: str = "644",
    ) -> bagit.Bag:
        """Create a new Bag if it does not exist."""
        assert self.upload_session, "This submission has no upload session!"
        assert self.metadata, "This submission has no associated metadata!"

        if not location.exists():
            location.mkdir(parents=True)

        # Clear any items in the location first
        self.remove_bag_contents(location)

        copied, missing = self.upload_session.copy_session_uploads(str(location))

        if missing:
            LOGGER.error("One or more uploaded files is missing!")
            LOGGER.info('Removing bag at "%s" due to missing files', location)
            self.remove_bag(location)
            raise FileNotFoundError(f"Could not create Bag due to {len(missing)} file(s) missing")

        LOGGER.info('Creating BagIt bag at "%s"', location)
        LOGGER.info("Using these checksum algorithm(s): %s", ", ".join(algorithms))

        bagit_info = self.metadata.create_flat_representation(version=ExportVersion.CAAIS_1_0)
        bag = bagit.make_bag(str(location), bagit_info, checksums=algorithms)

        LOGGER.info("Setting file mode for bag payload files to %s", file_perms)
        perms = int(file_perms, 8)
        for payload_file in bag.payload_files():
            payload_file_path = location / payload_file
            payload_file_path.chmod(perms)

        return bag

    def remove_bag(self, location: Path) -> None:
        """Remove everything in the Bag, including the Bag folder itself."""
        if not location.exists():
            return
        self.remove_bag_contents(location)
        location.rmdir()

    def remove_bag_contents(self, location: Path) -> None:
        """Remove everything in the Bag, but not the Bag directory itself."""
        if not location.exists():
            return
        for item in location.iterdir():
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)

    def __str__(self) -> str:
        """Get a string representation of this submission."""
        return f"Submission by {self.user} at {self.submission_date}"

    def __repr__(self) -> str:
        """Get a detailed string representation of this submission."""
        user = f"'{self.user.username}'" if self.user else "None"
        session = f"'{self.upload_session.token[0:8]}...'" if self.upload_session else "None"
        return f"<Submission(uuid='{self.uuid}', submission_date='{self.submission_date}' user={user}, upload_session={session})>"


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
        return f"{reverse('recordtransfer:submit')}?resume={self.uuid}"

    def get_delete_url(self) -> str:
        """Get the URL to delete this in-progress submission."""
        return reverse(
            "recordtransfer:delete_in_progress_submission_modal", kwargs={"uuid": self.uuid}
        )

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
