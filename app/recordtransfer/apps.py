import logging
import os
import re

from bagit import CHECKSUM_ALGOS
from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

LOGGER = logging.getLogger("recordtransfer")


def verify_email_settings() -> None:
    """Verify these settings.

    - DO_NOT_REPLY_USERNAME
    - ARCHIVIST_EMAIL

    Raises:
        ImproperlyConfigured: If either DO_NOT_REPLY_USERNAME or ARCHIVIST_EMAIL is empty.
    """
    if not settings.DO_NOT_REPLY_USERNAME:
        raise ImproperlyConfigured("The DO_NOT_REPLY_USERNAME setting is empty")
    if not settings.ARCHIVIST_EMAIL:
        raise ImproperlyConfigured("The ARCHIVIST_EMAIL setting is empty")


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

    - BAG_STORAGE_FOLDER
    - UPLOAD_STORAGE_FOLDER

    Creates the directories if they do not exist.

    Raises:
        ImproperlyConfigured: If the directories could not be created, or if they already exist
        exception if the directories could not be created, or if they already exist but as file.
    """
    for setting_name in [
        "BAG_STORAGE_FOLDER",
        "UPLOAD_STORAGE_FOLDER",
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
        if not isinstance(extensions, list) and not isinstance(extensions, set):
            raise ImproperlyConfigured(
                (
                    'The extension collection for the "{0}" group of the '
                    "ACCEPTED_FILE_FORMATS settings is the wrong type "
                    "(currently: {1}), should be list"
                ).format(group_name, type(extensions))
            )

        for i, extension in enumerate(extensions, 0):
            if not isinstance(extension, str):
                raise ImproperlyConfigured(
                    (
                        'The extension at index {0} in the "{1}" group of the '
                        "ACCEPTED_FILE_FORMATS settings is the wrong type "
                        "(currently: {2}), should be str"
                    ).format(i, group_name, type(extension))
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

            inverted_formats[extension] = group_name


def verify_caais_defaults() -> None:
    """Verify the settings.

    - CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE
    - CAAIS_DEFAULT_CREATION_TYPE

    Raises:
        ImproperlyConfigured: If either setting is empty.
    """
    if not settings.CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE:
        raise ImproperlyConfigured("CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE is not set")
    if not settings.CAAIS_DEFAULT_CREATION_TYPE:
        raise ImproperlyConfigured("CAAIS_DEFAULT_CREATION_TYPE is not set")


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
    for value, field in zip(fields, field_names):
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
        cron_str = settings.UPLOAD_SESSION_EXPIRED_CLEANUP_SCHEDULE
        if cron_str:
            _validate_cron(cron_str)
    except Exception as exc:
        raise ImproperlyConfigured(
            "UPLOAD_SESSION_EXPIRED_CLEANUP_SCHEDULE is not a valid cron string"
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
        settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES
        >= settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
    ):
        raise ImproperlyConfigured(
            "UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES must be less than "
            "UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES"
        )

    if (
        settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES <= 0
        and settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES != -1
    ):
        raise ImproperlyConfigured(
            "UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES must be greater than zero or -1"
        )


class RecordTransferConfig(AppConfig):
    """Top-level application config for the recordtransfer app."""

    name = "recordtransfer"

    def ready(self) -> None:
        """Verify the settings in the settings module."""
        try:
            LOGGER.info("Verifying settings in %s", settings.SETTINGS_MODULE)
            verify_email_settings()
            verify_date_format()
            verify_checksum_settings()
            verify_storage_folder_settings()
            verify_max_upload_size()
            verify_accepted_file_formats()
            verify_caais_defaults()

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
