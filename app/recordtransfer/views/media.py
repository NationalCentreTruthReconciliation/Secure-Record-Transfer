"""Views for handling media requests, such as uploading and deleting files. This also includes
viewing and listing uploaded files.
"""

import logging
from typing import cast

from clamav.scan import check_for_malware
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)
from django.utils.translation import gettext
from django.views.decorators.http import require_http_methods

from recordtransfer.decorators import require_upload_step
from recordtransfer.models import UploadSession, User
from recordtransfer.utils import accept_file, accept_session

LOGGER = logging.getLogger(__name__)


def media_request(request: HttpRequest, path: str) -> HttpResponse:
    """Respond to whether a media request is allowed or not."""
    if not request.user.is_authenticated:
        return HttpResponseForbidden("You do not have permission to access this resource.")

    if not path:
        return HttpResponseNotFound("The requested resource could not be found")

    user = request.user
    if not user.is_staff:
        return HttpResponseForbidden("You do not have permission to access this resource.")

    response = HttpResponse(headers={"X-Accel-Redirect": settings.MEDIA_URL + path.lstrip("/")})

    # Nginx will assign its own headers for the following:
    del response["Content-Type"]
    del response["Content-Disposition"]
    del response["Accept-Ranges"]
    del response["Set-Cookie"]
    del response["Cache-Control"]
    del response["Expires"]

    return response


@require_upload_step
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


@require_upload_step
@require_http_methods(["GET", "POST"])
def upload_or_list_files(request: HttpRequest, session_token: str) -> JsonResponse:
    """Upload a single file to the server list the files uploaded in a given upload session. The
    file is added to the upload session using the session token passed as a parameter in the
    request. If a session token is invalid, an error message is returned.

    The file type is checked against this application's ACCEPTED_FILE_FORMATS setting, if the
    file is not an accepted type, an error message is returned.

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
            file_metadata = [
                {"name": f.name, "size": f.file_upload.size, "url": f.get_file_access_url()}
                for f in session.get_uploads()
            ]

            return JsonResponse({"files": file_metadata}, status=200)
        else:
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

    except Exception as exc:
        LOGGER.error("Uncaught exception in upload_file view: %s", str(exc), exc_info=exc)
        return JsonResponse(
            {
                "error": gettext("There was an internal server error. Please try again."),
            },
            status=500,
        )


@require_upload_step
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
    try:
        session = UploadSession.objects.filter(token=session_token, user=request.user).first()
        if not session:
            return JsonResponse(
                {"error": gettext("Invalid filename or upload session token")}, status=404
            )

        if request.method == "DELETE":
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

        uploaded_file = None
        try:
            uploaded_file = session.get_temp_file_by_name(file_name)
        except FileNotFoundError:
            return JsonResponse(
                {"error": gettext("File not found in upload session")},
                status=404,
            )
        except ValueError:
            return JsonResponse(
                {"error": gettext("Cannot access file in upload session")},
                status=400,
            )

        file_url = uploaded_file.get_file_media_url()
        if settings.DEBUG:
            return HttpResponseRedirect(file_url)
        else:
            response = HttpResponse(headers={"X-Accel-Redirect": file_url})
            for header in [
                "Content-Type",
                "Content-Disposition",
                "Accept-Ranges",
                "Set-Cookie",
                "Cache-Control",
                "Expires",
            ]:
                del response[header]
            return response

    except Exception as exc:
        LOGGER.error("Error handling uploaded file: %s", str(exc), exc_info=exc)
        return JsonResponse({"error": gettext("Internal server error")}, status=500)
