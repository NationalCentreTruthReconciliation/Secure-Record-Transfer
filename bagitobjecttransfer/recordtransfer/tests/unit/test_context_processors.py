from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class TestSignupStatus(TestCase):
    def test_response_has_signup_status(self):
        response = self.client.get(reverse("recordtransfer:index"))
        self.assertEqual(
            response.context["SIGN_UP_ENABLED"], settings.SIGN_UP_ENABLED
        )


class TestFileUploadStatus(TestCase):
    def test_response_has_file_upload_status(self):
        response = self.client.get(reverse("recordtransfer:index"))
        self.assertEqual(
            response.context["FILE_UPLOAD_ENABLED"],
            settings.FILE_UPLOAD_ENABLED,
        )
