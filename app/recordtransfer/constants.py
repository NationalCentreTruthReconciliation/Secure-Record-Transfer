import dataclasses


@dataclasses.dataclass(frozen=True)
class HtmlIds:
    """Class to hold HTML element IDs used in the application."""

    # User Profile Form Field IDs
    ID_FIRST_NAME: str = "id_first_name"
    ID_LAST_NAME: str = "id_last_name"
    ID_GETS_NOTIFICATION_EMAILS: str = "id_gets_notification_emails"
    ID_CURRENT_PASSWORD: str = "id_current_password"
    ID_NEW_PASSWORD: str = "id_new_password"
    ID_CONFIRM_NEW_PASSWORD: str = "id_confirm_new_password"

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
class SubmissionFormWizardKeys:
    """Class to hold dictionary keys used in SubmissionFormWizard."""

    TEMPLATEREF: str = "templateref"
    FORMTITLE: str = "formtitle"
    INFOMESSAGE: str = "infomessage"
    FORM: str = "form"

    def asdict(self) -> dict[str, str]:
        """Return the dataclass as a dictionary."""
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class OtherValues:
    """Class to hold 'Other' option values used in dropdowns."""

    PROVINCE_OR_STATE: str = "Other"

    def asdict(self) -> dict[str, str]:
        """Return the dataclass as a dictionary."""
        return dataclasses.asdict(self)
