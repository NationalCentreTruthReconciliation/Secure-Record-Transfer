"""Custom decorators for the recordtransfer app."""

import functools
from typing import Callable

from django.http import HttpRequest, JsonResponse
from django.utils.translation import gettext

from recordtransfer.enums import SubmissionStep


def require_upload_step(view_func: Callable) -> Callable:
    """Restricts access to views based on the current wizard step. Only allows access if the
    request originates from the UPLOAD_FILES step of SubmissionFormWizard.
    """

    @functools.wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        # Check if request comes from the upload step
        wizard_data = request.session.get("wizard_transfer_form_wizard", {})
        current_step = wizard_data.get("step")

        # Allow access only if we're on the upload_files step
        if not current_step or current_step != SubmissionStep.UPLOAD_FILES.value:
            return JsonResponse(
                {"error": gettext("Uploads are only permitted during the file upload step")},
                status=403,
            )

        # Continue to the original view
        return view_func(request, *args, **kwargs)

    return _wrapped_view
