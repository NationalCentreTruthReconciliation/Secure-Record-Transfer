"""Custom decorators for the recordtransfer app."""

import functools
from typing import Callable

from django.http import HttpRequest, JsonResponse
from django.utils.translation import gettext

from recordtransfer.enums import SubmissionStep


def validate_upload_access(view_func: Callable) -> Callable:
    """Restricts access to views based on the current wizard step. Only allows POST requests
    during the UPLOAD_FILES step.
    """

    @functools.wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        # Check if request comes from the upload step
        wizard_data = request.session.get("wizard_submission_form_wizard", {})
        current_step = wizard_data.get("step")

        if not current_step or current_step not in [
            SubmissionStep.UPLOAD_FILES.value,
            SubmissionStep.REVIEW.value,
        ]:
            return JsonResponse(
                {"error": gettext("Access denied. Please try again.")},
                status=403,
            )

        # For POST requests, only allow during upload_files step
        if request.method == "POST" and current_step != SubmissionStep.UPLOAD_FILES.value:
            return JsonResponse(
                {"error": gettext("Uploads are only permitted during the file upload step")},
                status=403,
            )

        # Continue to the original view
        return view_func(request, *args, **kwargs)

    return _wrapped_view
