import logging
from typing import Optional
from uuid import UUID

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
from .handles import resolve_handle
from .html import sanitize_html_file
from .models import PermUploadedFile, TempUploadedFile, UploadSession

User = settings.AUTH_USER_MODEL

LOGGER = logging.getLogger(__name__)

#: HTTP header used to convey the opaque per-wizard upload handle for the
#: session-token-less upload endpoints.
UPLOAD_HANDLE_HEADER = "X-Upload-Handle"


@require_http_methods(["GET", "POST"])
def upload_or_list_files(request: HttpRequest) -> JsonResponse:
    """Upload a single file to the server list the files uploaded in a given upload session.

    The proper upload session is retrieved by way of accessing the request's session data. This
    must contain a valid upload handle to list or upload files. This ID is set by the form wizard.

    When uploading, the file type is checked against this application's
    :ref:`ACCEPTED_FILE_FORMATS` setting, if the file is not an accepted type, an error message is
    returned.

    Args:
        request: The HTTP GET or POST request
        session_token: The upload session token from the URL

    Returns:
        JsonResponse: If the list or upload operation was successful, the session token
        `uploadSessionToken` is included in the response. If not successful, the error description
        `error` is included.
    """
    try:
        session = resolve_handle(request, request.headers.get(UPLOAD_HANDLE_HEADER, ""))

        if not session:
            return JsonResponse(
                {"error": gettext("Invalid or expired upload session")},
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
        _file = sanitize_html_file(_file)
    except Exception as exc:
        LOGGER.error("Error sanitizing HTML file %s", _file.name, exc_info=exc)
        return JsonResponse(
            {
                "file": _file.name,
                "accepted": False,
                "uploadSessionToken": session.token,
                "error": gettext("There was an error processing the file"),
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
def uploaded_file_by_uuid(request: HttpRequest, file_uuid: UUID) -> HttpResponse:
    """Serve an uploaded file looked up by its opaque per-file UUID.

    Args:
        request: The HTTP request.
        file_uuid: The per-file UUID generated when the file was uploaded.

    Returns:
        HttpResponse: Redirects to the file's media path in development, or returns an
        X-Accel-Redirect in production. 404 if the file does not exist or is not accessible to the
        requester.
    """
    uploaded_file = (
        TempUploadedFile.objects.filter(uuid=file_uuid).first()
        or PermUploadedFile.objects.filter(uuid=file_uuid).first()
    )
    if uploaded_file is None:
        raise Http404(gettext("The uploaded file could not be found"))

    # Owners may access their own files; staff may access any file.
    if not request.user.is_staff and uploaded_file.session.user_id != request.user.id:
        LOGGER.error(
            "A non-staff user tried to access a file they do not have ownership over! User %s "
            "(id: %d) requested the file '%s' that they do not own.",
            request.user.username,
            request.user.pk,
            file_uuid,
        )
        raise Http404(gettext("The uploaded file could not be found"))

    try:
        file_url = uploaded_file.get_file_media_url()
    except FileNotFoundError as exc:
        LOGGER.error(
            "Tried to get a non-existent file '%s'",
            file_uuid,
            exc_info=exc,
        )
        raise Http404(gettext("The uploaded file could not be found")) from exc

    return serve_media_file(file_url)


@require_http_methods(["DELETE", "GET"])
def uploaded_file_by_name(request: HttpRequest, file_name: str) -> HttpResponse:
    """Get or delete a previously-uploaded file identified by the name and the upload handle.

    The upload session is resolved from the X-Upload-Handle header.

    Args:
        request: The HTTP DELETE or GET request. The header ``X-Upload-Handle`` must contain a
            valid handle previously registered by the form wizard.
        file_name: The name of the file to retrieve or delete

    Returns:
        HttpResponse:
            204 on successful DELETE; for GET, redirects to the file's media path in development,
            or returns an X-Accel-Redirect to the file's media path in production. 404 if the file
            or session cannot be resolved.
    """
    session = resolve_handle(request, request.headers.get(UPLOAD_HANDLE_HEADER, ""))

    if request.method == "DELETE":
        return _handle_uploaded_file_delete(session, file_name)

    return _handle_uploaded_file_get(session, file_name)


@require_http_methods(["GET"])
def uploaded_file_by_name_readonly(request: HttpRequest, file_name: str) -> HttpResponse:
    """Get a file that has been uploaded in a given upload session.

    This view is suitable for viewing files when file uploads are disabled. Otherwise, not having a
    DELETE request will make it so that users can't remove files from the upload files part of the
    form. Use ``uploaded_file_by_name`` for that instead.

    Args:
        request: The HTTP request
        file_name: The name of the file to retrieve

    Returns:
        HttpResponse:
            Redirects to the file's media path in development, or returns an X-Accel-Redirect to
            the file's media path if in production.
    """
    session = resolve_handle(request, request.headers.get(UPLOAD_HANDLE_HEADER, ""))
    return _handle_uploaded_file_get(session, file_name)


def _handle_uploaded_file_delete(session: Optional[UploadSession], file_name: str) -> HttpResponse:
    if not session:
        return JsonResponse(
            {"error": gettext("Invalid upload session")},
            status=404,
        )

    try:
        session.remove_temp_file_by_name(file_name)
    except FileNotFoundError as exc:
        LOGGER.error(
            "Tried to remove a non-existent file '%s' from session '%s'",
            file_name,
            session.token,
            exc_info=exc,
        )
        return JsonResponse(
            {"error": gettext("The uploaded file could not be found")},
            status=404,
        )
    except ValueError as exc:
        LOGGER.error(
            "An error occurred while trying to remove the file '%s' from session '%s'",
            file_name,
            session.token,
            exc_info=exc,
        )
        return JsonResponse(
            {"error": gettext("The uploaded file could not be deleted")},
            status=400,
        )
    return HttpResponse(status=204)


def _handle_uploaded_file_get(session: Optional[UploadSession], file_name: str) -> HttpResponse:
    if not session:
        raise Http404(gettext("The uploaded file could not be found"))

    try:
        uploaded_file = session.get_file_by_name(file_name)
    except FileNotFoundError as exc:
        LOGGER.error(
            "Tried to get a non-existent file '%s' from session '%s'",
            file_name,
            session.token,
            exc_info=exc,
        )
        raise Http404(gettext("The uploaded file could not be found")) from exc
    except ValueError as exc:
        LOGGER.error(
            "An error occurred while trying to get the file '%s' from session '%s'",
            file_name,
            session.token,
            exc_info=exc,
        )
        raise Http404(gettext("The uploaded file could not be found")) from exc

    try:
        file_url = uploaded_file.get_file_media_url()
    except FileNotFoundError as exc:
        LOGGER.error(
            "Tried to get a non-existent file '%s' from session '%s'",
            file_name,
            session.token,
            exc_info=exc,
        )
        raise Http404(gettext("The uploaded file could not be found")) from exc

    return serve_media_file(file_url)
