import json

from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpRequest, JsonResponse
from django.test import RequestFactory, TestCase
from django.utils.translation import gettext

from recordtransfer.decorators import require_upload_step
from recordtransfer.enums import SubmissionStep


class TestRequireUploadStepDecorator(TestCase):
    """Tests for the require_upload_step decorator."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.factory = RequestFactory()

    def test_request_without_wizard_data(self) -> None:
        """Requests without wizard data should be forbidden."""

        @require_upload_step
        def dummy_view(request: HttpRequest, *args, **kwargs):
            return JsonResponse({"success": True})

        for method in ["get", "post", "put", "delete"]:
            request = getattr(self.factory, method)("/dummy-url/")
            request.session = SessionStore()
            response = dummy_view(request)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                json.loads(response.content),
                {"error": gettext("Uploads are only permitted during the file upload step")},
            )

    def test_request_with_wrong_step(self) -> None:
        """Requests with the wrong wizard step should be forbidden."""

        @require_upload_step
        def dummy_view(request: HttpRequest, *args, **kwargs):
            return JsonResponse({"success": True})

        for method in ["get", "post", "put", "delete"]:
            request = getattr(self.factory, method)("/dummy-url/")
            request.session = SessionStore()
            request.session["wizard_submission_form_wizard"] = {"step": "some_other_step"}
            response = dummy_view(request)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                json.loads(response.content),
                {"error": gettext("Uploads are only permitted during the file upload step")},
            )

    def test_request_with_correct_step(self) -> None:
        """Requests with the correct wizard step should pass through."""

        @require_upload_step
        def dummy_view(request: HttpRequest, *args, **kwargs):
            return JsonResponse({"success": True})

        for method in ["get", "post", "put", "delete"]:
            request = getattr(self.factory, method)("/dummy-url/")
            request.session = SessionStore()
            request.session["wizard_submission_form_wizard"] = {
                "step": SubmissionStep.UPLOAD_FILES.value
            }
            request.session.save()
            response = dummy_view(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.content), {"success": True})
