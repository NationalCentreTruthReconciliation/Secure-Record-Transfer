import logging

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from recordtransfer.models import Job, User


@freeze_time("2024-01-15 10:30:00")
class TestJobFileView(TestCase):
    """Tests for recordtransfer:job_file view."""

    @classmethod
    def setUpClass(cls) -> None:
        """Disable logging."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls) -> None:
        """Create user accounts."""
        cls.staff_user = User.objects.create_user(
            username="staff", password="1X<ISRUkw+tuK", is_staff=True
        )
        cls.regular_user = User.objects.create_user(
            username="regular", password="1X<ISRUkw+tuK", is_staff=False
        )

    def setUp(self) -> None:
        """Set up test environment."""
        self.job_with_file = Job.objects.create(
            name="Test Job with File",
            description="A test job with an attached file",
            start_time=timezone.now(),
            user_triggered=self.staff_user,
            job_status=Job.JobStatus.COMPLETE,
        )

        self.job_without_file = Job.objects.create(
            name="Test Job without File",
            description="A test job without an attached file",
            start_time=timezone.now(),
            user_triggered=self.staff_user,
            job_status=Job.JobStatus.COMPLETE,
        )

        # Create and attach a file to job_with_file
        mock_file = SimpleUploadedFile(
            "test_report.pdf", b"test content", content_type="application/pdf"
        )
        self.job_with_file.attached_file.save("test_report.pdf", mock_file)

    def tearDown(self) -> None:
        """Clean up test data."""
        # Clean up any uploaded files
        for job in Job.objects.all():
            if job.attached_file:
                job.attached_file.delete()

        Job.objects.all().delete()

    def test_job_file_requires_staff_permission(self) -> None:
        """Test that the job_file view requires staff permission."""
        # Test with regular user (should be forbidden)
        self.client.login(username="regular", password="1X<ISRUkw+tuK")
        url = reverse("recordtransfer:job_file", kwargs={"job_uuid": self.job_with_file.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_job_file_requires_authentication(self) -> None:
        """Test that the job_file view requires authentication."""
        # Test without login (should redirect to login)
        url = reverse("recordtransfer:job_file", kwargs={"job_uuid": self.job_with_file.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_job_file_not_found(self) -> None:
        """Test accessing a non-existent job."""
        self.client.login(username="staff", password="1X<ISRUkw+tuK")
        import uuid

        non_existent_uuid = uuid.uuid4()
        url = reverse("recordtransfer:job_file", kwargs={"job_uuid": non_existent_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_job_file_no_attached_file(self) -> None:
        """Test accessing a job that has no attached file."""
        self.client.login(username="staff", password="1X<ISRUkw+tuK")
        url = reverse("recordtransfer:job_file", kwargs={"job_uuid": self.job_without_file.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_settings(DEBUG=True)
    def test_job_file_success_debug_mode(self) -> None:
        """Test successful file access in DEBUG mode."""
        self.client.login(username="staff", password="1X<ISRUkw+tuK")
        url = reverse("recordtransfer:job_file", kwargs={"job_uuid": self.job_with_file.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to file URL in debug mode
        # Check that the redirect URL contains the filename
        self.assertIn("test_report.pdf", response["Location"])

    @override_settings(DEBUG=False)
    def test_job_file_success_production_mode(self) -> None:
        """Test successful file access in production mode."""
        self.client.login(username="staff", password="1X<ISRUkw+tuK")
        url = reverse("recordtransfer:job_file", kwargs={"job_uuid": self.job_with_file.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Accel-Redirect", response.headers)
        self.assertTrue(response.headers["X-Accel-Redirect"].endswith("test_report.pdf"))

    @override_settings(DEBUG=False)
    def test_job_file_headers_zip_production_mode(self) -> None:
        """Test that a zip file has content headers in production mode."""
        self.client.login(username="staff", password="1X<ISRUkw+tuK")

        # Attach a new zip file to our job - replaces the PDF file
        zip_file = SimpleUploadedFile(
            "my_bag.zip", b"test content", content_type="application/zip"
        )
        self.job_with_file.attached_file.save("my_bag.zip", zip_file)

        response = self.client.get(
            reverse("recordtransfer:job_file", kwargs={"job_uuid": self.job_with_file.uuid})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["X-Accel-Redirect"].endswith("bag.zip"))
        self.assertIn(
            response["Content-Type"],
            ["application/zip", "application/x-zip-compressed"],
        )
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="my_bag.zip"')

    @override_settings(DEBUG=False)
    def test_job_file_headers_pdf_production_mode(self) -> None:
        """Test that a PDF file has content headers in production mode."""
        self.client.login(username="staff", password="1X<ISRUkw+tuK")

        response = self.client.get(
            reverse("recordtransfer:job_file", kwargs={"job_uuid": self.job_with_file.uuid})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["X-Accel-Redirect"].endswith("test_report.pdf"))
        self.assertIn("Content-Type", response.headers)
        self.assertIn("Content-Disposition", response.headers)
