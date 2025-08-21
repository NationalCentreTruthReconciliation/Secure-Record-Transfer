from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Q, query
from django.utils import timezone


class UploadSessionManager(models.Manager):
    """Custom manager for UploadSession model."""

    def get_expirable(self) -> query.QuerySet:
        """Return all expired upload sessions that can be set to EXPIRED.

        A session can be expired if it has not been interacted with in at least
        UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES minutes. Additionally, the session must be
        linked to an existing InProgressSubmission.

        If a session is *not* linked to an InProgressSubmission, and matches the same last
        interaction criteria above, then it will be returned by get_deletable instead.
        """
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
                UploadSession.SessionStatus.CREATED,  # type: ignore
                UploadSession.SessionStatus.UPLOADING,  # type: ignore
            ],
            in_progress_submission__isnull=False,
        )

    def get_deletable(self) -> query.QuerySet:
        """Return all upload sessions that can be safely deleted.

        An upload session that can be safely deleted matches these criteria:
        - It has expired (either by checking the last_upload_interaction_time, or the status)
        - It is not linked to an in-progress submission.

        If a session *is* linked to an InProgressSubmission, and matches the same last interaction
        criteria above, then it will be returned by get_expirable instead.
        """
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
            (
                Q(last_upload_interaction_time__lt=cutoff_time)
                & Q(
                    status__in=[
                        UploadSession.SessionStatus.CREATED,  # type: ignore
                        UploadSession.SessionStatus.UPLOADING,  # type: ignore
                    ]
                )
            )
            | Q(status=UploadSession.SessionStatus.EXPIRED),  # type: ignore
            in_progress_submission__isnull=True,
        )
