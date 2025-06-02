from typing import Any

from django.conf import settings
from django.http import HttpRequest

from recordtransfer import constants


def signup_status(request: HttpRequest) -> dict[str, Any]:
    """Add sign up status to template context."""
    return {"SIGN_UP_ENABLED": settings.SIGN_UP_ENABLED}


def file_upload_status(request: HttpRequest) -> dict[str, Any]:
    """Add file upload status to template context."""
    return {"FILE_UPLOAD_ENABLED": settings.FILE_UPLOAD_ENABLED}


def constants_context(request: HttpRequest) -> dict[str, str]:
    """Make constants available globally in all templates."""
    return {
        # User Profile Form Field IDs
        "ID_FIRST_NAME": constants.ID_FIRST_NAME,
        "ID_LAST_NAME": constants.ID_LAST_NAME,
        "ID_GETS_NOTIFICATION_EMAILS": constants.ID_GETS_NOTIFICATION_EMAILS,
        "ID_CURRENT_PASSWORD": constants.ID_CURRENT_PASSWORD,
        "ID_NEW_PASSWORD": constants.ID_NEW_PASSWORD,
        "ID_CONFIRM_NEW_PASSWORD": constants.ID_CONFIRM_NEW_PASSWORD,
        # Submission Group Form Field IDs
        "ID_SUBMISSION_GROUP_NAME": constants.ID_SUBMISSION_GROUP_NAME,
        "ID_SUBMISSION_GROUP_DESCRIPTION": constants.ID_SUBMISSION_GROUP_DESCRIPTION,
        "ID_SUBMISSION_GROUP_SELECTION": constants.ID_SUBMISSION_GROUP_SELECTION,
        "ID_DISPLAY_GROUP_DESCRIPTION": constants.ID_DISPLAY_GROUP_DESCRIPTION,
        # Contact Information Form Field IDs
        "ID_CONTACT_INFO_PROVINCE_OR_STATE": constants.ID_CONTACT_INFO_PROVINCE_OR_STATE,
        "ID_CONTACT_INFO_OTHER_PROVINCE_OR_STATE": constants.ID_CONTACT_INFO_OTHER_PROVINCE_OR_STATE,
        "OTHER_PROVINCE_OR_STATE_VALUE": constants.OTHER_PROVINCE_OR_STATE_VALUE,
        # Source Information Form Field IDs
        "ID_SOURCE_INFO_ENTER_MANUAL_SOURCE_INFO": constants.ID_SOURCE_INFO_ENTER_MANUAL_SOURCE_INFO,
        "ID_SOURCE_INFO_SOURCE_TYPE": constants.ID_SOURCE_INFO_SOURCE_TYPE,
        "ID_SOURCE_INFO_OTHER_SOURCE_TYPE": constants.ID_SOURCE_INFO_OTHER_SOURCE_TYPE,
        "ID_SOURCE_INFO_SOURCE_ROLE": constants.ID_SOURCE_INFO_SOURCE_ROLE,
        "ID_SOURCE_INFO_OTHER_SOURCE_ROLE": constants.ID_SOURCE_INFO_OTHER_SOURCE_ROLE,
        # Query Name Constants
        "PAGINATE_QUERY_NAME": constants.PAGINATE_QUERY_NAME,
        "SUBMISSION_GROUP_QUERY_NAME": constants.SUBMISSION_GROUP_QUERY_NAME,
        # Pagination Table Container IDs
        "ID_SUBMISSION_GROUP_TABLE": constants.ID_SUBMISSION_GROUP_TABLE,
        "ID_IN_PROGRESS_SUBMISSION_TABLE": constants.ID_IN_PROGRESS_SUBMISSION_TABLE,
        "ID_SUBMISSION_TABLE": constants.ID_SUBMISSION_TABLE,
    }
