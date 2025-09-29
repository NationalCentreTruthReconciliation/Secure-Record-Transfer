from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path
from typing import ClassVar, Iterable, Optional, Union

import bagit
from caais.export import ExportVersion
from caais.models import Metadata
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from upload.models import UploadSession

from recordtransfer.enums import SiteSettingKey, SiteSettingType, SubmissionStep
from recordtransfer.managers import InProgressSubmissionManager
from recordtransfer.storage import OverwriteStorage

LOGGER = logging.getLogger(__name__)

# Sentinel object to distinguish between cache miss and cached None values
NOT_CACHED = object()


class User(AbstractUser):
    """The main User object used to authenticate users."""

    # User preferences
    gets_submission_email_updates = models.BooleanField(default=False)
    gets_notification_emails = models.BooleanField(default=True)
    language = models.CharField(
        max_length=7,
        blank=True,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
        help_text=_("Preferred language for the website and email notifications"),
        verbose_name=_("Preferred Language"),
    )

    # Contact information
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

    def open_upload_sessions(self) -> models.QuerySet[UploadSession]:
        """Get the upload sessions this user has open.

        An "open" upload session is one in any of these states:

        - CREATED
        - UPLOADING
        - COPYING_IN_PROGRESS

        Returns:
            The open upload sessions for this user, in no particular order.
        """
        return UploadSession.objects.filter(
            user=self,
            status__in=[
                UploadSession.SessionStatus.CREATED,
                UploadSession.SessionStatus.UPLOADING,
                UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            ],
        )

    def open_sessions_within_limit(self, will_add_new: bool = False) -> bool:
        """Determine if this user's total upload session count is within the limit set.

        The upload session limit is set by :ref:`UPLOAD_SESSION_MAX_CONCURRENT_OPEN`.

        Args:
            will_add_new:
                Find whether the current session count PLUS a new one would put the count over the
                limit. Defaults to False.

        Returns:
            True if less than or equal to the limit, False if over the limit.
        """
        # If feature is disabled, always return True
        if settings.UPLOAD_SESSION_MAX_CONCURRENT_OPEN == -1:
            return True

        count = self.open_upload_sessions().count()
        if will_add_new:
            count += 1

        return count <= settings.UPLOAD_SESSION_MAX_CONCURRENT_OPEN

    def past_password_hashes(self, limit: int = 5) -> list:
        """Get the past N hashes of this user's previous password."""
        hashes = self.password_history.order_by("-changed_at")[:limit]
        return list(hashes.values_list("password", flat=True))


class PasswordHistory(models.Model):
    """Store a user's previous password hashes for history validation."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_history")
    password = models.CharField(max_length=255)  # hashed password
    changed_at = models.DateTimeField(auto_now_add=True)


@receiver(pre_save, sender=User)
def add_previous_password_to_history(instance: User, **kwargs) -> None:
    """Handle password history when User password changes."""
    if not instance.pk:  # New user, no password history needed
        return

    # Skip password history during fixture loading to avoid race conditions
    if kwargs.get("raw", False):
        return

    try:
        # Get the old password from the database
        old_instance = User.objects.get(pk=instance.pk)
        old_password = old_instance.password

        if old_password != instance.password:
            PasswordHistory.objects.create(
                user=instance, password=old_password, changed_at=timezone.now()
            )
            LOGGER.info(
                "Password history created for user: username='%s', user_id=%s",
                instance.username,
                instance.pk,
            )

    except User.DoesNotExist:
        LOGGER.debug("User %s does not exist yet, skipping password history", instance.pk)
    except Exception as e:
        LOGGER.error("Error creating password history for user %s: %s", instance.pk, str(e))


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
    def number_of_submissions_in_group(self) -> int:
        """Get the number of submissions in this group."""
        return len(self.submission_set.all())

    def get_absolute_url(self) -> str:
        """Return the URL to access a detail view of this submission group."""
        return reverse("recordtransfer:submission_group_detail", kwargs={"uuid": self.uuid})

    def get_delete_url(self) -> str:
        """Return the URL to delete this submission group."""
        return reverse("recordtransfer:delete_submission_group_modal", kwargs={"uuid": self.uuid})

    def __str__(self):
        """Return a string representation of this object."""
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

        _copied, missing = self.upload_session.copy_session_uploads(str(location))

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

    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
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

    def has_file(self) -> bool:
        """Determine if this job has an attached file."""
        return bool(self.attached_file)

    def get_file_media_url(self) -> str:
        """Generate the media URL to this file.

        Raises:
            FileNotFoundError if the file does not exist.
        """
        if self.has_file():
            return self.attached_file.url
        raise FileNotFoundError(f"{self.name} does not exist in job {self.uuid}")

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


@receiver(pre_delete, sender=InProgressSubmission)
def delete_upload_session_on_delete(
    sender: InProgressSubmission, instance: InProgressSubmission, **kwargs
) -> None:
    """Delete the upload session for a given in progress submission when it's deleted."""
    if instance.upload_session:
        instance.upload_session.delete()


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
