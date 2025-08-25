"""Views for handling downloading media."""

import logging

from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
)
from django.shortcuts import get_object_or_404
from nginx.serve import serve_media_file

from recordtransfer.models import Job

LOGGER = logging.getLogger(__name__)


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
