import dataclasses


@dataclasses.dataclass(frozen=True)
class HtmlIds:
    """Class to hold HTML element IDs used in the application."""

    # User Profile Form Field IDs
    ID_FIRST_NAME: str = "id_first_name"
    ID_LAST_NAME: str = "id_last_name"
    ID_GETS_NOTIFICATION_EMAILS: str = "id_gets_notification_emails"

    # Submission Group Form Field IDs
    ID_SUBMISSION_GROUP_NAME: str = "id_submission_group_name"
    ID_SUBMISSION_GROUP_DESCRIPTION: str = "id_submission_group_description"

    # Submission Group Selection and Description Display Element IDs
    ID_SUBMISSION_GROUP_SELECTION: str = "id_submission_group_selection"
    ID_DISPLAY_GROUP_DESCRIPTION: str = "id_display_group_description"

    # Contact Information Form Field IDs
    ID_CONTACT_INFO_PROVINCE_OR_STATE: str = "id_contactinfo-province_or_state"
    ID_CONTACT_INFO_OTHER_PROVINCE_OR_STATE: str = "id_contactinfo-other_province_or_state"

    # Source Information Form Field IDs
    ID_SOURCE_INFO_ENTER_MANUAL_SOURCE_INFO: str = "id_sourceinfo-enter_manual_source_info"
    ID_SOURCE_INFO_SOURCE_TYPE: str = "id_sourceinfo-source_type"
    ID_SOURCE_INFO_OTHER_SOURCE_TYPE: str = "id_sourceinfo-other_source_type"
    ID_SOURCE_INFO_SOURCE_ROLE: str = "id_sourceinfo-source_role"
    ID_SOURCE_INFO_OTHER_SOURCE_ROLE: str = "id_sourceinfo-other_source_role"

    # Pagination Table Container IDs
    ID_SUBMISSION_GROUP_TABLE: str = "submission-group-table-container"
    ID_IN_PROGRESS_SUBMISSION_TABLE: str = "in-progress-submission-table-container"
    ID_SUBMISSION_TABLE: str = "submission-table-container"

    def asdict(self) -> dict[str, str]:
        """Return the dataclass as a dictionary."""
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class QueryParameters:
    """Class to hold query parameter names used in the application."""

    PAGINATE_QUERY_NAME: str = "p"
    SUBMISSION_GROUP_QUERY_NAME: str = "group"

    def asdict(self) -> dict[str, str]:
        """Return the class attributes as a dictionary."""
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class OtherValues:
    """Class to hold 'Other' option values used in dropdowns."""

    PROVINCE_OR_STATE: str = "Other"

    def asdict(self) -> dict[str, str]:
        """Return the dataclass as a dictionary."""
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class FormFieldNames:
    """Class to hold form field names used in POST requests."""

    # Submission Group Assignment Form Field Names
    SUBMISSION_UUID: str = "submission_uuid"
    GROUP_UUID: str = "group_uuid"
    UNASSIGN_GROUP: str = "unassign_group"

    def asdict(self) -> dict[str, str]:
        """Return the dataclass as a dictionary."""
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class HeaderNames:
    """Class to hold header names used in HTTP requests."""

    FRONTEND_REQUEST: str = "X-Requested-By-Frontend"

    def asdict(self) -> dict[str, str]:
        """Return the dataclass as a dictionary."""
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WindowsFileRestrictions:
    """Windows file size limits and reserved file names."""

    MAX_FILENAME_LENGTH: int = 256
    RESERVED_FILENAMES: tuple = (
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    )


@dataclasses.dataclass(frozen=True)
class FileExtensions:
    """Class to hold file extension sets used in the application."""

    COMPRESSED: tuple = (
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
    )

    def asdict(self) -> dict[str, str]:
        """Return the dataclass as a dictionary."""
        return dataclasses.asdict(self)
