from django.test import TestCase
from django.urls import reverse

import bagitobjecttransfer.settings.base


class TestSignupStatus(TestCase):
    def test_response_has_signup_status(self):
        response = self.client.get(reverse("recordtransfer:index"))
        self.assertEqual(
            response.context["SIGN_UP_ENABLED"], bagitobjecttransfer.settings.base.SIGN_UP_ENABLED
        )


class TestFileUploadStatus(TestCase):
    def test_response_has_file_upload_status(self):
        response = self.client.get(reverse("recordtransfer:index"))
        self.assertEqual(
            response.context["FILE_UPLOAD_ENABLED"],
            bagitobjecttransfer.settings.base.FILE_UPLOAD_ENABLED,
        )


class TestFileUploadLimit(TestCase):
    def test_response_has_max_total_size(self):
        response = self.client.get(reverse("recordtransfer:index"))
        self.assertEqual(
            response.context["MAX_TOTAL_UPLOAD_SIZE"],
            bagitobjecttransfer.settings.base.MAX_TOTAL_UPLOAD_SIZE,
        )

    def test_response_has_max_single_size(self):
        response = self.client.get(reverse("recordtransfer:index"))
        self.assertEqual(
            response.context["MAX_SINGLE_UPLOAD_SIZE"],
            bagitobjecttransfer.settings.base.MAX_SINGLE_UPLOAD_SIZE,
        )

    def test_response_has_max_count(self):
        response = self.client.get(reverse("recordtransfer:index"))
        self.assertEqual(
            response.context["MAX_TOTAL_UPLOAD_COUNT"],
            bagitobjecttransfer.settings.base.MAX_TOTAL_UPLOAD_COUNT,
        )
