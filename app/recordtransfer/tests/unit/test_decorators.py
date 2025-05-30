import json

from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpRequest, JsonResponse
from django.test import RequestFactory, TestCase
from django.utils.translation import gettext

from recordtransfer.decorators import validate_upload_access
from recordtransfer.enums import SubmissionStep


class TestRequireUploadStepDecorator(TestCase):
    """Tests for the require_upload_step decorator."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.factory = RequestFactory()

    def test_request_without_wizard_data(self) -> None:
        """Requests without wizard data should be forbidden."""

        @validate_upload_access
        def dummy_view(request: HttpRequest, *args, **kwargs):
            return JsonResponse({"success": True})

        for method in ["get", "post", "put", "delete"]:
            request = getattr(self.factory, method)("/dummy-url/")
            request.session = SessionStore()
            response = dummy_view(request)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                json.loads(response.content),
                {"error": gettext("Access denied. Please try again.")},
            )

    def test_request_with_wrong_step(self) -> None:
        """Requests with the wrong wizard step should be forbidden."""

        @validate_upload_access
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
                {"error": gettext("Access denied. Please try again.")},
            )

    def test_post_request_during_upload_step(self) -> None:
        """POST requests during the UPLOAD_FILES step should be allowed."""

        @validate_upload_access
        def dummy_view(request: HttpRequest, *args, **kwargs):
            return JsonResponse({"success": True})

        request = self.factory.post("/dummy-url/")
        request.session = SessionStore()
        request.session["wizard_submission_form_wizard"] = {
            "step": SubmissionStep.UPLOAD_FILES.value
        }
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"success": True})

    def test_post_request_during_review_step(self) -> None:
        """POST requests during the REVIEW step should be forbidden."""

        @validate_upload_access
        def dummy_view(request: HttpRequest, *args, **kwargs):
            return JsonResponse({"success": True})

        request = self.factory.post("/dummy-url/")
        request.session = SessionStore()
        request.session["wizard_submission_form_wizard"] = {"step": SubmissionStep.REVIEW.value}
        response = dummy_view(request)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content),
            {"error": gettext("Uploads are only permitted during the file upload step")},
        )

    def test_post_request_during_other_step(self) -> None:
        """POST requests during any step other than UPLOAD_FILES should be forbidden."""

        @validate_upload_access
        def dummy_view(request: HttpRequest, *args, **kwargs):
            return JsonResponse({"success": True})

        for step in SubmissionStep:
            if step == SubmissionStep.UPLOAD_FILES or step == SubmissionStep.REVIEW:
                continue

            request = self.factory.post("/dummy-url/")
            request.session = SessionStore()
            request.session["wizard_submission_form_wizard"] = {"step": step.value}
            response = dummy_view(request)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                json.loads(response.content),
                {"error": gettext("Access denied. Please try again.")},
            )

    def test_get_request_during_upload_step(self) -> None:
        """GET requests during the UPLOAD_FILES step should be allowed."""

        @validate_upload_access
        def dummy_view(request: HttpRequest, *args, **kwargs):
            return JsonResponse({"success": True})

        request = self.factory.get("/dummy-url/")
        request.session = SessionStore()
        request.session["wizard_submission_form_wizard"] = {
            "step": SubmissionStep.UPLOAD_FILES.value
        }
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"success": True})

    def test_get_request_during_review_step(self) -> None:
        """GET requests during the REVIEW step should be allowed."""

        @validate_upload_access
        def dummy_view(request: HttpRequest, *args, **kwargs):
            return JsonResponse({"success": True})

        request = self.factory.get("/dummy-url/")
        request.session = SessionStore()
        request.session["wizard_submission_form_wizard"] = {"step": SubmissionStep.REVIEW.value}
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"success": True})

    def test_delete_request_during_upload_step(self) -> None:
        """DELETE requests during the UPLOAD_FILES step should be allowed."""

        @validate_upload_access
        def dummy_view(request: HttpRequest, *args, **kwargs):
            return JsonResponse({"success": True})

        request = self.factory.delete("/dummy-url/")
        request.session = SessionStore()
        request.session["wizard_submission_form_wizard"] = {
            "step": SubmissionStep.UPLOAD_FILES.value
        }
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"success": True})

    def test_delete_request_during_other_step(self) -> None:
        """DELETE requests during any step other than UPLOAD_FILES should be forbidden."""

        @validate_upload_access
        def dummy_view(request: HttpRequest, *args, **kwargs):
            return JsonResponse({"success": True})

        for step in SubmissionStep:
            if step == SubmissionStep.UPLOAD_FILES or step == SubmissionStep.REVIEW:
                continue

            request = self.factory.delete("/dummy-url/")
            request.session = SessionStore()
            request.session["wizard_submission_form_wizard"] = {"step": step.value}
            response = dummy_view(request)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                json.loads(response.content),
                {"error": gettext("Access denied. Please try again.")},
            )
