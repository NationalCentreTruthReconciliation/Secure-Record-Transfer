from bagitobjecttransfer.settings.base import (
    FILE_UPLOAD_ENABLED,
    MAX_SINGLE_UPLOAD_SIZE,
    MAX_TOTAL_UPLOAD_SIZE,
    SIGN_UP_ENABLED,
)
from bagitobjecttransfer.settings.base import (
    MAX_TOTAL_UPLOAD_COUNT,
)


def signup_status(request):
    return {"SIGN_UP_ENABLED": SIGN_UP_ENABLED}


def file_upload_status(request):
    return {"FILE_UPLOAD_ENABLED": FILE_UPLOAD_ENABLED}


def file_uploads(request):
    return {
        "MAX_TOTAL_UPLOAD_SIZE": MAX_TOTAL_UPLOAD_SIZE,
        "MAX_SINGLE_UPLOAD_SIZE": MAX_SINGLE_UPLOAD_SIZE,
        "MAX_TOTAL_UPLOAD_COUNT": MAX_TOTAL_UPLOAD_COUNT,
    }
