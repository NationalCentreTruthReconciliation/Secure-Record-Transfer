import logging
import os
import re

from bagit import CHECKSUM_ALGOS
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand

from recordtransfer.utils import is_deployed_environment

LOGGER = logging.getLogger(__name__)

COMPRESSED_FILE_EXTENSIONS = {
    "7z",
    "aar",
    "ace",
    "arj",
    "apk",
    "arc",
    "ark",
    "br",
    "bz",
    "bz2",
    "cab",
    "chm",
    "deb",
    "dmg",
    "ear",
    "egg",
    "epub",
    "gz",
    "jar",
    "lha",
    "lrz",
    "lz",
    "lz4",
    "lzh",
    "lzma",
    "lzo",
    "lzop",
    "mar",
    "par2",
    "pea",
    "pet",
    "pkg",
    "rar",
    "rpm",
    "rz",
    "s7z",
    "shar",
    "sit",
    "sitx",
    "tbz",
    "tbz2",
    "tgz",
    "tlz",
    "txz",
    "tzo",
    "war",
    "whl",
    "xpi",
    "xz",
    "z",
    "zip",
    "zipx",
    "zoo",
    "zpaq",
    "zst",
}


class Command(BaseCommand):
    """Verify application settings defined in the DJANGO_SETTINGS_MODULE."""

    help = "Verify application settings."

    def handle(self, *args, **options) -> None:
        """Verify application settings."""
        try:
            LOGGER.info("Verifying settings in %s", settings.SETTINGS_MODULE)
            verify_date_format()
            verify_checksum_settings()
            verify_storage_folder_settings()
            verify_max_upload_size()
            verify_accepted_file_formats()
            verify_upload_session_expiry_settings()
            verify_site_id()
            if is_deployed_environment():
                verify_security_settings()
                verify_recaptcha_settings()

        except AttributeError as exc:
            match_obj = re.search(r'has no attribute ["\'](.+)["\']', str(exc), re.IGNORECASE)
            if match_obj:
                setting_name = match_obj.group(1)
                raise ImproperlyConfigured(
                    ("The {0} setting is not defined in {1}!").format(
                        setting_name, settings.SETTINGS_MODULE
                    )
                ) from exc
            raise exc


def verify_date_format() -> None:
    """Verify the setting.

    - APPROXIMATE_DATE_FORMAT

    Raises:
        ImproperlyConfigured: If the setting does not contain "{date}".
    """
    if r"{date}" not in settings.APPROXIMATE_DATE_FORMAT:
        raise ImproperlyConfigured(
            ("The APPROXIMATE_DATE_FORMAT (currently: {0}) does not contain {{date}}").format(
                settings.APPROXIMATE_DATE_FORMAT
            )
        )


def verify_checksum_settings() -> None:
    """Verify the setting.

    - BAG_CHECKSUMS

    Raises:
        ImproperlyConfigured: If the setting is empty or contains unsupported checksum algorithms.
    """
    if not settings.BAG_CHECKSUMS:
        raise ImproperlyConfigured(
            "No checksums found in the BAG_CHECKSUMS setting. Choose one "
            "or more checksum algorithms to generate checksums for when "
            'creating a BagIt bag, separated by commas (i.e., "sha1,sha256")'
        )
    not_found = [a for a in settings.BAG_CHECKSUMS if a not in CHECKSUM_ALGOS]
    if not_found:
        not_supported = ", ".join(not_found)
        supported = ", ".join(CHECKSUM_ALGOS)
        raise ImproperlyConfigured(
            (
                "These algorithm(s) found in the BAG_CHECKSUMS setting are NOT "
                "supported: {0}. The algorithms that ARE supported are: {1}."
            ).format(not_supported, supported)
        )


def verify_storage_folder_settings() -> None:
    """Verify the settings.

    - UPLOAD_STORAGE_FOLDER
    - TEMP_STORAGE_FOLDER

    Creates the directories if they do not exist.

    Raises:
        ImproperlyConfigured: If the directories could not be created, or if they already exist
        exception if the directories could not be created, or if they already exist but as file.
    """
    for setting_name in [
        "UPLOAD_STORAGE_FOLDER",
        "TEMP_STORAGE_FOLDER",
    ]:
        directory = getattr(settings, setting_name)

        if os.path.exists(directory) and os.path.isfile(directory):
            raise ImproperlyConfigured(
                (
                    "The {0} at {1} is a file. Remove this file or change the {0} "
                    "to a different folder"
                ).format(setting_name, directory)
            )

        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                LOGGER.info("Created %s at %s", setting_name, directory)
            except PermissionError as exc:
                raise ImproperlyConfigured(
                    (
                        "Could not create the {0} at the path {1}. Ensure "
                        "permissions are configured so that this folder can be "
                        "created, or create it manually."
                    ).format(setting_name, directory)
                ) from exc


def verify_max_upload_size() -> None:
    """Verify the settings.

    - MAX_TOTAL_UPLOAD_SIZE_MB
    - MAX_SINGLE_UPLOAD_SIZE_MB
    - MAX_TOTAL_UPLOAD_COUNT

    Raises:
        ImproperlyConfigured: If any are less than or equal to zero, or if the single upload size
        is greater than the total upload size.
    """
    for setting_name in [
        "MAX_TOTAL_UPLOAD_SIZE_MB",
        "MAX_SINGLE_UPLOAD_SIZE_MB",
        "MAX_TOTAL_UPLOAD_COUNT",
    ]:
        value = getattr(settings, setting_name)

        if not isinstance(value, int):
            raise ImproperlyConfigured(
                ("The {0} setting is the wrong type (currently: {1}), should be int").format(
                    setting_name, type(value)
                )
            )

        if value == 0:
            raise ImproperlyConfigured(
                ("The {0} setting is set to ZERO, it cannot be less than 1").format(setting_name)
            )

        if value < 0:
            raise ImproperlyConfigured(
                ("The {0} setting is negative (currently: {1}), it cannot be less than 1").format(
                    setting_name, value
                )
            )

    max_total_size = settings.MAX_TOTAL_UPLOAD_SIZE_MB
    max_single_size = settings.MAX_SINGLE_UPLOAD_SIZE_MB
    if max_total_size < max_single_size:
        raise ImproperlyConfigured(
            (
                "The MAX_TOTAL_UPLOAD_SIZE_MB setting (currently: {0}) cannot be less "
                "than the MAX_SINGLE_UPLOAD_SIZE_MB setting (currently: {1})"
            ).format(max_total_size, max_single_size)
        )


def _validate_extension_format(extension: str, group_name: str) -> None:
    """Validate a single file extension format.

    Args:
        extension: The file extension to validate.
        group_name: The group name containing this extension.

    Raises:
        ImproperlyConfigured: If the extension format is invalid.
    """
    if not isinstance(extension, str):
        raise ImproperlyConfigured(
            (
                'The extension in the "{0}" group of the '
                "ACCEPTED_FILE_FORMATS settings is the wrong type "
                "(currently: {1}), should be str"
            ).format(group_name, type(extension))
        )

    if extension[0] == ".":
        raise ImproperlyConfigured(
            (
                'The file extension "{0}" in the "{1}" group of the '
                "ACCEPTED_FILE_FORMATS setting starts with a period (.), "
                "file extensions should not start with periods"
            ).format(extension, group_name)
        )

    match_obj = re.match(r"^[a-z0-9][\.a-z0-9]*[a-z0-9]$", extension)
    if not match_obj:
        raise ImproperlyConfigured(
            (
                'The file extension "{0}" in the "{1}" group of the '
                "ACCEPTED_FILE_FORMATS setting is invalid. File extensions "
                "may only contain lowercase letters and numbers, and MAY "
                "contain periods EXCEPT at the start and end of the "
                "extension name"
            ).format(extension, group_name)
        )


def _check_extension_duplicates(extension: str, group_name: str, inverted_formats: dict) -> None:
    """Check for duplicate extensions across groups.

    Args:
        extension: The file extension to check.
        group_name: The current group name.
        inverted_formats: Dictionary mapping extensions to their group names.

    Raises:
        ImproperlyConfigured: If the extension appears in multiple groups.
    """
    if extension in inverted_formats:
        last_seen_group = inverted_formats[extension]

        if last_seen_group == group_name:
            raise ImproperlyConfigured(
                (
                    'The file extension "{0}" appears more than once in '
                    'the "{1}" group of the ACCEPTED_FILE_FORMATS setting. '
                    "Ensure each extension appears only once across all "
                    "groups"
                ).format(extension, group_name)
            )

        raise ImproperlyConfigured(
            (
                'The file extension "{0}" appears across more than one '
                "group in the ACCEPTED_FILE_FORMATS setting (appears in "
                'the "{1}" and "{2}" groups). Ensure each extension '
                "appears only once across all groups"
            ).format(extension, group_name, last_seen_group)
        )


def verify_accepted_file_formats() -> None:
    """Verify the setting.

    - ACCEPTED_FILE_FORMATS

    Raises:
        ImproperlyConfigured exception if there are any issues with the formatting of the setting
        or the file extensions in the setting.
    """
    formats = settings.ACCEPTED_FILE_FORMATS

    if not isinstance(formats, dict):
        raise ImproperlyConfigured(
            (
                "The ACCEPTED_FILE_FORMATS setting is the wrong type (currently: "
                "{0}), should be dict"
            ).format(type(formats))
        )

    if not formats:
        raise ImproperlyConfigured("The ACCEPTED_FILE_FORMATS setting is empty")

    inverted_formats = {}

    for group_name, extensions in formats.items():
        if not isinstance(extensions, set):
            raise ImproperlyConfigured(
                (
                    'The extension collection for the "{0}" group of the '
                    "ACCEPTED_FILE_FORMATS settings is the wrong type "
                    "(currently: {1}), should be set"
                ).format(group_name, type(extensions))
            )

        for extension in extensions:
            _validate_extension_format(extension, group_name)
            _check_extension_duplicates(extension, group_name, inverted_formats)
            inverted_formats[extension] = group_name

    _check_for_compressed_files(inverted_formats)


def _check_for_compressed_files(inverted_formats: dict) -> None:
    """Check for compressed file extensions in accepted formats and print warning.

    Args:
        inverted_formats: Dictionary mapping extensions to their group names.
    """
    found_compressed = []

    for extension in inverted_formats:
        if extension in COMPRESSED_FILE_EXTENSIONS:
            found_compressed.append(extension)

    if found_compressed:
        warning_msg = [
            "",
            "********************************************************************************",
            "******* !! WARNING !!",
            "******* You've enabled uploads of compressed file collections (.zip, .7z, ...)",
            "******* Analyzing compressed files is not supported yet, it is possible for",
            "******* malicious files to be uploaded like this.",
            "******* Consider removing this file type from ACCEPTED_FILE_FORMATS",
            "********************************************************************************",
            f"******* Found compressed extensions: {', '.join(found_compressed)}",
            "********************************************************************************",
            "",
        ]

        LOGGER.warning("\n".join(warning_msg))


def _validate_cron(cron_str: str) -> None:
    """Validate a cron expression.

    Args:
        cron_str: The cron expression to validate.

    Raises:
        ValueError: If the cron expression is invalid.
    """
    # Check number of fields
    fields = cron_str.strip().split()
    if len(fields) != 5:
        raise ValueError("Cron expression must have 5 fields")

    # Regex for each cron field
    cron_patterns = {
        "minute": r"^(?:\*(?:/[1-9]\d*)?|[0-5]?\d(?:-[0-5]?\d)?(?:/[1-9]\d*)?(?:,[0-5]?\d)*)$",
        "hour": r"^(?:\*(?:/[1-9]\d*)?|[01]?\d|2[0-3](?:-[01]?\d|2[0-3])?(?:/[1-9]\d*)?(?:,[01]?\d|2[0-3])*)$",
        "day_of_month": r"^(?:\*(?:/[1-9]\d*)?|[1-9]|[12]\d|3[01](?:-[1-9]|[12]\d|3[01])?(?:/[1-9]\d*)?(?:,[1-9]|[12]\d|3[01])*)$",
        "month": r"^(?:\*(?:/[1-9]\d*)?|[1-9]|1[0-2](?:-[1-9]|1[0-2])?(?:/[1-9]\d*)?(?:,[1-9]|1[0-2])*)$",
        "day_of_week": r"^(?:\*(?:/[1-9]\d*)?|[0-6](?:-[0-6])?(?:/[1-9]\d*)?(?:,[0-6])*)$",
    }

    field_names = ["minute", "hour", "day_of_month", "month", "day_of_week"]

    # Validate each field
    for value, field in zip(fields, field_names, strict=True):
        pattern = cron_patterns[field]
        if not re.match(pattern, value):
            raise ValueError(f"Invalid value '{value}' for field '{field}'")


def verify_upload_session_expiry_settings() -> None:
    """Verify the settings.

    - UPLOAD_SESSION_EXPIRED_CLEANUP_SCHEDULE
    - UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
    - UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES

    Raises:
        ImproperlyConfigured: If the expiry schedule is not a valid cron string, or if the
        expiry settings are invalid.
    """
    try:
        cleanup_schedule = settings.UPLOAD_SESSION_EXPIRED_CLEANUP_SCHEDULE
        if cleanup_schedule:
            _validate_cron(cleanup_schedule)
    except ValueError as exc:
        raise ImproperlyConfigured(
            "UPLOAD_SESSION_EXPIRED_CLEANUP_SCHEDULE is not a valid cron string"
        ) from exc

    try:
        email_schedule = settings.IN_PROGRESS_SUBMISSION_EXPIRING_EMAIL_SCHEDULE
        if email_schedule:
            _validate_cron(email_schedule)
    except ValueError as exc:
        raise ImproperlyConfigured(
            "IN_PROGRESS_SUBMISSION_EXPIRING_EMAIL_SCHEDULE is not a valid cron string"
        ) from exc

    if (
        settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES <= 0
        and settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES != -1
    ):
        raise ImproperlyConfigured(
            "UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES must be greater than zero or -1"
        )

    if (
        settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES <= 0
        and settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES != -1
    ):
        raise ImproperlyConfigured(
            "UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES must be greater than zero or -1"
        )

    if (
        settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES != -1
        and settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES != -1
        and settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES
        >= settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
    ):
        raise ImproperlyConfigured(
            "UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES must be less than "
            "UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES"
        )


def verify_site_id() -> None:
    """Verify that the SITE_ID setting is valid."""
    site_id = settings.SITE_ID
    if not Site.objects.filter(pk=site_id).exists():
        raise ImproperlyConfigured(
            f"Site with ID {site_id} does not exist. Check the configured SITE_ID"
        )


def verify_axes_settings() -> None:
    """Verify Axes settings."""
    if not settings.AXES_ENABLED:
        LOGGER.debug("AXES is disabled, skipping verification.")
        return
    if settings.AXES_FAILURE_LIMIT <= 0:
        raise ImproperlyConfigured("AXES_FAILURE_LIMIT must be greater than zero")

    if settings.AXES_WARNING_THRESHOLD <= 0:
        raise ImproperlyConfigured("AXES_WARNING_THRESHOLD must be greater than zero")

    if settings.AXES_WARNING_THRESHOLD >= settings.AXES_FAILURE_LIMIT:
        raise ImproperlyConfigured("AXES_WARNING_THRESHOLD must be less than AXES_FAILURE_LIMIT")

    if settings.AXES_COOLOFF_TIME <= 0:
        raise ImproperlyConfigured("AXES_COOLOFF_TIME must be a float greater than zero")


def verify_security_settings() -> None:
    """Verify SECRET_KEY value is set."""
    secret_key = getattr(settings, "SECRET_KEY", "")
    if not secret_key:
        raise ImproperlyConfigured("SECRET_KEY is required. Generate a secure secret key.")

    LOGGER.info("Verified SECRET_KEY is set.")


def verify_recaptcha_settings() -> None:
    """Verify Recaptcha settings."""
    if not getattr(settings, "RECAPTCHA_PUBLIC_KEY", ""):
        raise ImproperlyConfigured(
            "RECAPTCHA_PUBLIC_KEY is required in production environments. "
            "Set this to a valid reCAPTCHA public key."
        )

    if not getattr(settings, "RECAPTCHA_PRIVATE_KEY", ""):
        raise ImproperlyConfigured(
            "RECAPTCHA_PRIVATE_KEY is required in production environments. "
            "Set this to a valid reCAPTCHA private key."
        )

    LOGGER.info("reCAPTCHA is properly configured.")
