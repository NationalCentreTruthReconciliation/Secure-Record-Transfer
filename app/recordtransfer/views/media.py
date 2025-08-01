"""Views for handling media requests, such as uploading and deleting files. This also includes
viewing and listing uploaded files.
"""

import logging
from pathlib import Path
from typing import Optional, cast

from clamav.scan import check_for_malware
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from django.views.decorators.http import require_http_methods

from recordtransfer.decorators import validate_upload_access
from recordtransfer.models import Job, UploadSession, User
from recordtransfer.utils import accept_file, accept_session

LOGGER = logging.getLogger(__name__)


def serve_media_file(file_url: str) -> HttpResponse:
    """Create a response that allows a client to download a media file.

    In development, the development server serves media files directly, so a re-direct to the
    file's URL is returned.

    In production, NGINX is used, and it serves media files. The media URL is locked down with an
    "internal" directive, and NGINX must receive an X-Accel-Redirect from the application to tell
    it that it's OK to serve the file.

    For more info, see:
    `NGINX docs <https://nginx.org/en/docs/http/ngx_http_core_module.html#internal>`_

    .. note::

       This function does not do any permission checking. Make sure the client that is asking for a
       file has the proper permission before calling this function.

    Args:
        file_url: The media URL to serve

    Returns:
        HttpResponse: Direct redirect in development (DEBUG) mode, X-Accel-Redirect in production
    """
    if settings.DEBUG:
        return HttpResponseRedirect(file_url)
    else:
        headers = {"X-Accel-Redirect": file_url}

        # NGINX will change the file name if we do not set these headers
        if file_url.endswith(".zip"):
            headers["Content-Type"] = "application/zip"
            headers["Content-Disposition"] = f'attachment; filename="{Path(file_url).name}"'

        response = HttpResponse(headers=headers)

        # Clear headers
        for remove in [
            "Content-Type",
            "Content-Disposition",
            "Accept-Ranges",
            "Set-Cookie",
            "Cache-Control",
            "Expires",
        ]:
            if remove in response.headers and remove not in headers:
                del response[remove]

        return response


@validate_upload_access
@require_http_methods(["POST"])
def create_upload_session(request: HttpRequest) -> JsonResponse:
    """Create a new upload session and return the session token.

    Args:
        request: The POST request sent by the user.

    Returns:
        JsonResponse: The session token of the newly created upload session.
    """
    try:
        user: User = cast(User, request.user)
        session = UploadSession.new_session(user=user)
        return JsonResponse({"uploadSessionToken": session.token}, status=201)
    except Exception as exc:
        LOGGER.error("Error creating upload session: %s", str(exc), exc_info=exc)
        return JsonResponse(
            {"error": gettext("There was an internal server error. Please try again.")},
            status=500,
        )


@validate_upload_access
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

    file_check = accept_file(_file.name, _file.size)
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
                "error": gettext(f'Malware was detected in the file "{_file.name}"'),
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
        raise Http404("The uploaded file could not be found")

    try:
        uploaded_file = session.get_file_by_name(file_name)
    except (FileNotFoundError, ValueError) as exc:
        raise Http404("The uploaded file could not be found") from exc

    file_url = uploaded_file.get_file_media_url()
    return serve_media_file(file_url)


def job_file(request: HttpRequest, job_uuid: str) -> HttpResponse:
    """View to access the attached file associated with a job.

    Args:
        request: The HTTP request
        job_uuid: The UUID of the job

    Returns:
        HttpResponse: Redirects to the file's media path if the job has an associated file.
    """
    if not request.user.is_staff:
        raise Http404("The requested resource could not be found")

    job = get_object_or_404(Job, uuid=job_uuid)

    if not job.has_file():
        raise Http404("File not found for this job")

    file_url = job.get_file_media_url()
    return serve_media_file(file_url)
