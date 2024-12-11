from django.conf import settings


def signup_status(request):
    return {"SIGN_UP_ENABLED": settings.SIGN_UP_ENABLED}


def file_upload_status(request):
    return {"FILE_UPLOAD_ENABLED": settings.FILE_UPLOAD_ENABLED}


def file_uploads(request):
    return {
        "MAX_TOTAL_UPLOAD_SIZE": settings.MAX_TOTAL_UPLOAD_SIZE,
        "MAX_SINGLE_UPLOAD_SIZE": settings.MAX_SINGLE_UPLOAD_SIZE,
        "MAX_TOTAL_UPLOAD_COUNT": settings.MAX_TOTAL_UPLOAD_COUNT,
    }
