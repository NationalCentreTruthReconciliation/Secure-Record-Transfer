"""Tests for the admin module."""

from unittest.mock import Mock

from django.test import RequestFactory, TestCase

from recordtransfer.admin import PermUploadedFileInline, TempUploadedFileInline, UploadSessionAdmin
from recordtransfer.models import UploadSession


class TestUploadSessionAdmin(TestCase):
    """Test cases for UploadSessionAdmin."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.admin = UploadSessionAdmin(UploadSession, Mock())
        self.request = RequestFactory().get("/")

    def test_get_inlines_with_created_status(self) -> None:
        """Test get_inlines returns TempUploadedFileInline for CREATED status."""
        obj = Mock(spec=UploadSession)
        obj.status = UploadSession.SessionStatus.CREATED

        result = self.admin.get_inlines(self.request, obj)

        self.assertEqual(result, [TempUploadedFileInline])

    def test_get_inlines_with_uploading_status(self) -> None:
        """Test get_inlines returns TempUploadedFileInline for UPLOADING status."""
        obj = Mock(spec=UploadSession)
        obj.status = UploadSession.SessionStatus.UPLOADING

        result = self.admin.get_inlines(self.request, obj)

        self.assertEqual(result, [TempUploadedFileInline])

    def test_get_inlines_with_expired_status(self) -> None:
        """Test get_inlines returns TempUploadedFileInline for EXPIRED status."""
        obj = Mock(spec=UploadSession)
        obj.status = UploadSession.SessionStatus.EXPIRED

        result = self.admin.get_inlines(self.request, obj)

        self.assertEqual(result, [TempUploadedFileInline])

    def test_get_inlines_with_stored_status(self) -> None:
        """Test get_inlines returns PermUploadedFileInline for STORED status."""
        obj = Mock(spec=UploadSession)
        obj.status = UploadSession.SessionStatus.STORED

        result = self.admin.get_inlines(self.request, obj)

        self.assertEqual(result, [PermUploadedFileInline])

    def test_get_inlines_with_other_status(self) -> None:
        """Test get_inlines returns both inlines for any other status."""
        obj = Mock(spec=UploadSession)
        obj.status = "SOME_OTHER_STATUS"

        result = self.admin.get_inlines(self.request, obj)

        self.assertEqual(result, [TempUploadedFileInline, PermUploadedFileInline])

    def test_get_inlines_with_none_obj(self) -> None:
        """Test get_inlines returns no inlines when obj is None."""
        result = self.admin.get_inlines(self.request, None)

        self.assertEqual(result, [])
