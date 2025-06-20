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


def constants_context(request: HttpRequest) -> dict[str, Any]:
    """Make constants available globally in all templates."""
    return {
        **constants.HtmlIds().asdict(),
        **constants.QueryParameters().asdict(),
        "ACCEPTED_FILE_FORMATS": settings.ACCEPTED_FILE_FORMATS,  # This is key
    }
