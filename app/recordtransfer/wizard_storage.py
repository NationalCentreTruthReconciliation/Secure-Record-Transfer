import copy
from typing import Any, Optional

from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.utils import timezone
from formtools.wizard.storage.base import BaseStorage

from recordtransfer.enums import SubmissionStep
from recordtransfer.models import InProgressSubmission

LEGACY_WIZARD_DATA_VERSION = 1
WIZARD_DATA_VERSION = 2


def initial_wizard_data(
    current_step: str,
    extra_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Return a canonical, initialized formtools storage envelope."""
    return {
        "version": WIZARD_DATA_VERSION,
        "wizard": {
            BaseStorage.step_key: current_step,
            BaseStorage.step_data_key: {},
            BaseStorage.step_files_key: {},
            BaseStorage.extra_data_key: extra_data or {},
        },
    }


class InProgressSubmissionStorage(BaseStorage):
    """Store formtools wizard data in an ``InProgressSubmission``.

    The previous save-for-later implementation wrapped formtools' storage data in ``past`` and
    kept the unvalidated current step and extra data alongside it. This storage reads that legacy
    shape without rewriting it until the wizard data changes.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.in_progress_submission = self._get_in_progress_submission()
        self.legacy_current_data: dict | list[dict] | None = None
        self._finalized = False
        self._data = self._load_data()
        self._original_data = copy.deepcopy(self._data)

    def _get_in_progress_submission(self) -> InProgressSubmission:
        """Return the owner-scoped in-progress submission named by the request."""
        submission_uuid = self.request.GET.get("resume") if self.request else None
        if not submission_uuid or not self.request.user.is_authenticated:
            raise Http404("In-progress submission not found")

        try:
            return InProgressSubmission.objects.get(
                uuid=submission_uuid,
                user=self.request.user,
            )
        except (InProgressSubmission.DoesNotExist, ValidationError, ValueError) as exc:
            raise Http404("In-progress submission not found") from exc

    def _empty_data(self) -> dict[str, Any]:
        """Return initialized formtools data for this submission."""
        return {
            self.step_key: self.in_progress_submission.current_step,
            self.step_data_key: {},
            self.step_files_key: {},
            self.extra_data_key: {},
        }

    def _normalize_data(self, data: object) -> dict[str, Any]:
        """Ensure persisted JSON contains every key required by ``BaseStorage``."""
        normalized = self._empty_data()
        if isinstance(data, dict):
            for key in normalized:
                if key in data:
                    normalized[key] = copy.deepcopy(data[key])

        # The model field remains the source of truth while legacy rows are supported.
        normalized[self.step_key] = self.in_progress_submission.current_step
        return normalized

    def _load_data(self) -> dict[str, Any]:
        """Load canonical data, or adapt the legacy save-for-later envelope."""
        persisted = self.in_progress_submission.step_data
        if not persisted:
            return self._empty_data()
        if not isinstance(persisted, dict):
            raise ValueError("Invalid in-progress submission wizard data")

        if persisted.get("version") == WIZARD_DATA_VERSION:
            return self._normalize_data(persisted.get("wizard"))

        if persisted.get("version") == LEGACY_WIZARD_DATA_VERSION:
            data = self._normalize_data(persisted.get("past"))
            legacy_extra = persisted.get("extra")
            if isinstance(legacy_extra, dict):
                data[self.extra_data_key].update(copy.deepcopy(legacy_extra))

            legacy_current = persisted.get("current")
            if isinstance(legacy_current, (dict, list)):
                self.legacy_current_data = copy.deepcopy(legacy_current)
            return data

        raise ValueError("Unsupported in-progress submission wizard data version")

    @property
    def data(self) -> dict[str, Any]:
        """Return the mutable formtools data for this request."""
        return self._data

    @data.setter
    def data(self, value: dict[str, Any]) -> None:
        self._data = value

    def _get_accession_title(self) -> tuple[bool, Optional[str]]:
        """Derive the draft title from serialized record-description data when present."""
        step = SubmissionStep.RECORD_DESCRIPTION.value
        field = f"{step}-accession_title"
        step_data = self.data[self.step_data_key].get(step)
        if isinstance(step_data, dict) and field in step_data:
            value = step_data[field]
            if isinstance(value, list):
                value = value[-1] if value else ""
            return True, str(value) or None

        if (
            self.in_progress_submission.current_step == step
            and isinstance(self.legacy_current_data, dict)
            and "accession_title" in self.legacy_current_data
        ):
            value = self.legacy_current_data["accession_title"]
            return True, str(value) or None

        return False, None

    def _save(self) -> None:
        """Persist changed wizard data and synchronized model projections."""
        if self._finalized or self.data == self._original_data:
            return

        current_step = self.data.get(self.step_key) or self.in_progress_submission.current_step
        self.in_progress_submission.current_step = current_step
        self.in_progress_submission.step_data = {
            "version": WIZARD_DATA_VERSION,
            "wizard": copy.deepcopy(self.data),
        }
        self.in_progress_submission.last_updated = timezone.now()

        update_fields = ["current_step", "step_data", "last_updated"]
        title_found, title = self._get_accession_title()
        if title_found:
            self.in_progress_submission.title = title
            update_fields.append("title")

        self.in_progress_submission.save(update_fields=update_fields)
        self._original_data = copy.deepcopy(self.data)
        self.legacy_current_data = None

    def mark_finalized(self) -> None:
        """Prevent formtools' final reset from rewriting a deleted draft."""
        self._finalized = True

    def update_response(self, response: HttpResponse) -> None:
        """Flush changed database state, then perform formtools file cleanup."""
        self._save()
        super().update_response(response)
