from unittest.mock import patch

from django.http import Http404, HttpResponse, QueryDict
from django.test import RequestFactory, TestCase

from recordtransfer.enums import SubmissionStep
from recordtransfer.models import InProgressSubmission, UploadSession, User
from recordtransfer.wizard_storage import (
    LEGACY_WIZARD_DATA_VERSION,
    WIZARD_DATA_VERSION,
    InProgressSubmissionStorage,
)


class InProgressSubmissionStorageTests(TestCase):
    """Tests for database-backed submission wizard storage."""

    def setUp(self) -> None:
        """Create a request factory and wizard owner."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="storage-user", password="password")

    def _storage(self, submission: InProgressSubmission) -> InProgressSubmissionStorage:
        request = self.factory.get("/submission/", {"resume": submission.uuid})
        request.user = self.user
        return InProgressSubmissionStorage("submission_form_wizard", request=request)

    def test_loads_canonical_wizard_data(self) -> None:
        """Canonical data is exposed through the standard formtools storage interface."""
        wizard_data = {
            "step": SubmissionStep.CONTACT_INFO.value,
            "step_data": {"acceptlegal": {"acceptlegal-agreement_accepted": ["on"]}},
            "step_files": {},
            "extra_data": {"prompted": True},
        }
        submission = InProgressSubmission.objects.create(
            user=self.user,
            current_step=SubmissionStep.CONTACT_INFO.value,
            step_data={"version": WIZARD_DATA_VERSION, "wizard": wizard_data},
        )

        storage = self._storage(submission)

        self.assertEqual(storage.data, wizard_data)
        self.assertIsNone(storage.legacy_current_data)

    def test_loads_legacy_data_without_rewriting_it(self) -> None:
        """Legacy data is adapted in memory and left unchanged on a read-only request."""
        legacy_data = {
            "version": LEGACY_WIZARD_DATA_VERSION,
            "past": {
                "step": SubmissionStep.ACCEPT_LEGAL.value,
                "step_data": {},
                "step_files": {},
                "extra_data": {"from_past": True},
            },
            "current": {"contact_name": "Legacy Donor"},
            "extra": {"from_extra": True},
        }
        submission = InProgressSubmission.objects.create(
            user=self.user,
            current_step=SubmissionStep.CONTACT_INFO.value,
            step_data=legacy_data,
        )
        storage = self._storage(submission)

        with patch.object(storage.in_progress_submission, "save") as save:
            storage.update_response(HttpResponse())

        self.assertEqual(storage.current_step, SubmissionStep.CONTACT_INFO.value)
        self.assertEqual(storage.extra_data, {"from_past": True, "from_extra": True})
        self.assertEqual(storage.legacy_current_data, {"contact_name": "Legacy Donor"})
        save.assert_not_called()
        submission.refresh_from_db()
        self.assertEqual(submission.step_data, legacy_data)

    def test_rejects_unversioned_wizard_data(self) -> None:
        """Non-empty persisted data must identify its schema explicitly."""
        submission = InProgressSubmission.objects.create(
            user=self.user,
            current_step=SubmissionStep.CONTACT_INFO.value,
            step_data={"past": {}},
        )

        with self.assertRaisesRegex(ValueError, "Unsupported.*version"):
            self._storage(submission)

    def test_persists_nested_changes_in_canonical_format(self) -> None:
        """Nested formtools mutations trigger a canonical database write."""
        submission = InProgressSubmission.objects.create(
            user=self.user,
            current_step=SubmissionStep.RECORD_DESCRIPTION.value,
        )
        storage = self._storage(submission)
        data = QueryDict(mutable=True)
        data["recorddescription-accession_title"] = "Autosaved submission"

        storage.set_step_data(SubmissionStep.RECORD_DESCRIPTION.value, data)
        storage.current_step = SubmissionStep.RIGHTS.value
        storage.extra_data["save_contact_info_prompted"] = True
        storage.update_response(HttpResponse())

        submission.refresh_from_db()
        self.assertEqual(submission.current_step, SubmissionStep.RIGHTS.value)
        self.assertEqual(submission.title, "Autosaved submission")
        self.assertEqual(submission.step_data["version"], WIZARD_DATA_VERSION)
        self.assertEqual(
            submission.step_data["wizard"]["extra_data"],
            {"save_contact_info_prompted": True},
        )

    def test_persisting_session_token_attaches_owned_upload_session(self) -> None:
        """The draft relationship is synchronized from an owner-validated legacy token."""
        submission = InProgressSubmission.objects.create(
            user=self.user,
            current_step=SubmissionStep.GROUP_SUBMISSION.value,
        )
        upload_session = UploadSession.new_session(user=self.user)
        storage = self._storage(submission)

        storage.extra_data["session_token"] = upload_session.token
        storage.save()

        submission.refresh_from_db()
        self.assertEqual(submission.upload_session, upload_session)

    def test_does_not_attach_another_users_upload_session(self) -> None:
        """A persisted token cannot associate an upload session owned by another user."""
        submission = InProgressSubmission.objects.create(
            user=self.user,
            current_step=SubmissionStep.GROUP_SUBMISSION.value,
        )
        other_user = User.objects.create_user(username="session-owner", password="password")
        upload_session = UploadSession.new_session(user=other_user)
        storage = self._storage(submission)

        storage.extra_data["session_token"] = upload_session.token
        storage.save()

        submission.refresh_from_db()
        self.assertIsNone(submission.upload_session)

    def test_rejects_submission_owned_by_another_user(self) -> None:
        """A user cannot load another user's wizard data by UUID."""
        other_user = User.objects.create_user(username="other-user", password="password")
        submission = InProgressSubmission.objects.create(
            user=other_user,
            current_step=SubmissionStep.ACCEPT_LEGAL.value,
        )

        with self.assertRaises(Http404):
            self._storage(submission)
