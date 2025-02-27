import csv
from io import StringIO

from caais.export import ExportVersion
from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import query
from django.http import HttpResponse
from django.utils import timezone


class SubmissionQuerySet(query.QuerySet):
    """Adds the ability to export a queryset as a CSV."""

    def export_csv(
        self, version: ExportVersion = ExportVersion.CAAIS_1_0, filename_prefix=None
    ) -> HttpResponse:
        """Create an HttpResponse that contains a CSV representation of all submissions in the
        queryset.

        Args:
            version (ExportVersion): The type/version of the CSV to export
        """
        csv_file = StringIO()
        writer = csv.writer(csv_file)
        first_row = True

        for submission in self:
            row = submission.metadata.create_flat_representation(version)
            if first_row:
                writer.writerow(row.keys())
                first_row = False
            writer.writerow(row.values())

        csv_file.seek(0)

        response = HttpResponse(csv_file, content_type="text/csv")

        local_time = timezone.localtime(timezone.now()).strftime(r"%Y%m%d_%H%M%S")
        if not filename_prefix:
            version_bits = str(version).split("_")
            filename_prefix = "{0}_v{1}_".format(
                version_bits[0], ".".join([str(x) for x in version_bits[1:]])
            )

        filename = f"{filename_prefix}{local_time}.csv"
        response["Content-Disposition"] = f"attachment; filename={filename}"
        csv_file.close()
        return response


class UploadSessionManager(models.Manager):
    """Custom manager for UploadSession model."""

    def get_expirable(self) -> query.QuerySet:
        """Return all expired upload sessions that can be set to EXPIRED."""
        if settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES == -1:
            return self.none()

        cutoff_time = timezone.now() - timezone.timedelta(
            minutes=settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
        )

        # Avoiding circular import
        UploadSession = apps.get_model(
            app_label="recordtransfer",
            model_name="UploadSession",
        )

        return self.filter(
            last_upload_interaction_time__lt=cutoff_time,
            status__in=[
                UploadSession.SessionStatus.CREATED,
                UploadSession.SessionStatus.UPLOADING,
            ],
        )

    def get_deletable(self) -> query.QuerySet:
        """Return all upload sessions that can be deleted. A session is deletable if it is EXPIRED
        and not associated with any in-progress submissions.
        """
        if settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES == -1:
            return self.none()

        # Avoiding circular import
        UploadSession = apps.get_model(
            app_label="recordtransfer",
            model_name="UploadSession",
        )

        return self.filter(
            status__in=[
            UploadSession.SessionStatus.EXPIRED,
            ],
            inprogresssubmission__isnull=True,
        )


class InProgressSubmissionManager(models.Manager):
    """Custom manager for InProgressSubmission model."""

    def get_expiring_without_reminder(self) -> query.QuerySet:
        """Return all in-progress submissions with upload sessions that are about to expire and
        have not had a reminder email sent.
        """
        if (
            settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES == -1
            or settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES == -1
        ):
            return self.none()

        # Upload sessions with a last interaction time that is less than this cutoff time will
        # expire soon
        cutoff_time = timezone.now() - timezone.timedelta(
            minutes=(
                settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
                - settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES
            )
        )

        # Avoiding circular import
        UploadSession = apps.get_model(
            app_label="recordtransfer",
            model_name="UploadSession",
        )

        # Get submissions with active upload sessions that will expire soon
        return self.filter(
            reminder_email_sent=False,
            upload_session__isnull=False,
            upload_session__last_upload_interaction_time__lt=cutoff_time,
            upload_session__status__in=[
                UploadSession.SessionStatus.CREATED,
                UploadSession.SessionStatus.UPLOADING,
            ],
        )
