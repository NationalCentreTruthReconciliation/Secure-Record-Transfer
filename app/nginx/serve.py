from pathlib import Path

from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
)
from upload.mime import mime


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

        # Determine MIME type based on file extension and set headers deterministically
        file_path = Path(file_url)
        extension = file_path.suffix.lower().lstrip(".")
        mime_types = mime.guess(extension)
        if mime_types:
            # Sort MIME types to ensure deterministic behavior
            sorted_mime_types = sorted(mime_types)
            headers["Content-Type"] = sorted_mime_types[0]
            headers["Content-Disposition"] = f'attachment; filename="{file_path.name}"'

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
