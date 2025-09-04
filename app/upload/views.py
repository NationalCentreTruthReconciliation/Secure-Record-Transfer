import logging
from typing import Optional, cast

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    JsonResponse,
)
from django.utils.translation import gettext
from django.views.decorators.http import require_http_methods
from nginx.serve import serve_media_file

from .check import accept_file, accept_session
from .clam import check_for_malware
from .models import UploadSession

User = settings.AUTH_USER_MODEL

LOGGER = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def upload_or_list_files(request: HttpRequest, session_token: str) -> JsonResponse:
    """Upload a single file to the server list the files uploaded in a given upload session. The
    file is added to the upload session using the session token passed as a parameter in the
    request. If a session token is invalid, an error message is returned.

    The file type is checked against this application's :ref:`ACCEPTED_FILE_FORMATS` setting, if
    the file is not an accepted type, an error message is returned.

    Args:
        request: The HTTP GET or POST request
        session_token: The upload session token from the URL

    Returns:
        JsonResponse: If the list or upload operation was successful, the session token
        `uploadSessionToken` is included in the response. If not successful, the error description
        `error` is included.
    """
    try:
        user: User = cast(User, request.user)
        session = UploadSession.objects.filter(token=session_token, user=user).first()
        if not session:
            return JsonResponse(
                {
                    "uploadSessionToken": session_token,
                    "error": gettext("Invalid upload session token"),
                },
                status=400,
            )

        if request.method == "GET":
            return _handle_list_files(session)
        else:
            return _handle_upload_file(request, session)

    except Exception as exc:
        LOGGER.error("Uncaught exception in upload_file view: %s", str(exc), exc_info=exc)
        return JsonResponse(
            {
                "error": gettext("There was an internal server error. Please try again."),
            },
            status=500,
        )


def _handle_list_files(session: UploadSession) -> JsonResponse:
    file_metadata = [
        {"name": f.name, "size": f.file_upload.size, "url": f.get_file_access_url()}
        for f in session.get_uploads()
    ]
    return JsonResponse({"files": file_metadata}, status=200)


def _handle_upload_file(request: HttpRequest, session: UploadSession) -> JsonResponse:
    _file = request.FILES.get("file")
    if not _file:
        return JsonResponse(
            {
                "uploadSessionToken": session.token,
                "error": gettext("No file was uploaded"),
            },
            status=400,
        )

    file_check = accept_file(_file.name, _file.size, _file)
    if not file_check["accepted"]:
        return JsonResponse(
            {"file": _file.name, "uploadSessionToken": session.token, **file_check},
            status=400,
        )

    session_check = accept_session(_file.name, _file.size, session)
    if not session_check["accepted"]:
        return JsonResponse(
            {"file": _file.name, "uploadSessionToken": session.token, **session_check},
            status=400,
        )

    try:
        check_for_malware(_file)
    except ValidationError as exc:
        LOGGER.error("Malware was found in the file %s", _file.name, exc_info=exc)
        return JsonResponse(
            {
                "file": _file.name,
                "accepted": False,
                "uploadSessionToken": session.token,
                "error": gettext('Malware was detected in the file "%(name)s"')
                % {"name": _file.name},
            },
            status=400,
        )
    except ValueError as exc:
        LOGGER.error("File too large for malware scanning: %s", _file.name, exc_info=exc)
        return JsonResponse(
            {
                "file": _file.name,
                "accepted": False,
                "uploadSessionToken": session.token,
                "error": gettext('File "%(name)s" is too large to scan for malware')
                % {"name": _file.name},
            },
            status=400,
        )
    except ConnectionError as exc:
        LOGGER.error("ClamAV connection error for file %s", _file.name, exc_info=exc)
        return JsonResponse(
            {
                "file": _file.name,
                "accepted": False,
                "uploadSessionToken": session.token,
                "error": gettext("Unable to scan file for malware due to scanner error"),
            },
            status=500,
        )

    try:
        uploaded_file = session.add_temp_file(_file)
    except ValueError as exc:
        LOGGER.error("Error adding file to session: %s", str(exc), exc_info=exc)
        return JsonResponse(
            {
                "file": _file.name,
                "accepted": False,
                "uploadSessionToken": session.token,
                "error": gettext("There was an error uploading the file"),
            },
            status=500,
        )

    file_url = uploaded_file.get_file_access_url()

    return JsonResponse(
        {
            "file": _file.name,
            "accepted": True,
            "uploadSessionToken": session.token,
            "url": file_url,
        },
        status=200,
    )


@require_http_methods(["GET"])
def readonly_uploaded_file(
    request: HttpRequest, session_token: str, file_name: str
) -> HttpResponse:
    """Get a file that has been uploaded in a given upload session.

    This view is suitable for viewing files when file uploads are disabled. Otherwise, not having a
    DELETE request will make it so that users can't remove files from the upload files part of the
    form. Use ``uploaded_file`` for that instead.

    Args:
        request: The HTTP request
        session_token: The upload session token from the URL
        file_name: The name of the file to delete

    Returns:
        HttpResponse:
            Redirects to the file's media path in development, or returns an X-Accel-Redirect to
            the file's media path if in production.
    """
    if request.user.is_staff:
        session = UploadSession.objects.filter(token=session_token).first()
    else:
        session = UploadSession.objects.filter(token=session_token, user=request.user).first()

    return _handle_uploaded_file_get(session, file_name)


@require_http_methods(["DELETE", "GET"])
def uploaded_file(request: HttpRequest, session_token: str, file_name: str) -> HttpResponse:
    """Get or delete a file that has been uploaded in a given upload session.

    Args:
        request: The HTTP request
        session_token: The upload session token from the URL
        file_name: The name of the file to delete

    Returns:
        HttpResponse:
            In the case of deletion, returns a 204 response when successfully deleted. In the case
            of getting a file, redirects to the file's media path in development, or returns an
            X-Accel-Redirect to the file's media path if in production.
    """
    if request.user.is_staff:
        session = UploadSession.objects.filter(token=session_token).first()
    else:
        session = UploadSession.objects.filter(token=session_token, user=request.user).first()

    if request.method == "DELETE":
        return _handle_uploaded_file_delete(session, file_name)
    else:
        return _handle_uploaded_file_get(session, file_name)


def _handle_uploaded_file_delete(session: Optional[UploadSession], file_name: str) -> HttpResponse:
    if not session:
        return JsonResponse(
            {"error": gettext("Invalid filename or upload session token")},
            status=404,
        )

    try:
        session.remove_temp_file_by_name(file_name)
    except FileNotFoundError:
        return JsonResponse(
            {"error": gettext("File not found in upload session")},
            status=404,
        )
    except ValueError:
        return JsonResponse(
            {"error": gettext("Cannot remove file from upload session")},
            status=400,
        )
    return HttpResponse(status=204)


def _handle_uploaded_file_get(session: Optional[UploadSession], file_name: str) -> HttpResponse:
    if not session:
        raise Http404(gettext("The uploaded file could not be found"))

    try:
        uploaded_file = session.get_file_by_name(file_name)
    except (FileNotFoundError, ValueError) as exc:
        raise Http404("The uploaded file could not be found") from exc

    file_url = uploaded_file.get_file_media_url()
    return serve_media_file(file_url)
