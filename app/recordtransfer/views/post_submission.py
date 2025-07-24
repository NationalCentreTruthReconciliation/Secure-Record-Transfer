"""Views for completed submissions, and creating and managing submission groups."""

import logging
from typing import Any, Optional, cast

from caais.export import ExportVersion
from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, UpdateView
from django_htmx.http import trigger_client_event

from recordtransfer.constants import HtmlIds, QueryParameters
from recordtransfer.forms.submission_group_form import SubmissionGroupForm
from recordtransfer.models import Submission, SubmissionGroup, User

LOGGER = logging.getLogger(__name__)


class SubmissionDetailView(DetailView):
    """Generates a report for a given submission."""

    model = Submission
    template_name = "recordtransfer/submission_detail.html"
    context_object_name = "submission"

    def get_object(self, queryset: Optional[QuerySet] = None) -> Submission:
        """Retrieve the Submission object based on the UUID in the URL."""
        if queryset is None:
            queryset = self.get_queryset()

        return get_object_or_404(queryset, uuid=self.kwargs.get("uuid"))

    def get_queryset(self) -> QuerySet[SubmissionGroup]:
        """Return queryset filtered by user permissions."""
        queryset = super().get_queryset()

        if self.request.user.is_staff:
            return queryset
        else:
            return queryset.filter(user=self.request.user)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Pass context variables to the template."""
        context = super().get_context_data(**kwargs)
        context["current_date"] = timezone.now()
        context["metadata"] = context["submission"].metadata
        return context


@require_http_methods(["GET"])
def submission_csv_export(request: HttpRequest, uuid: str) -> HttpResponse:
    """Generate and download a CSV for a specific submission."""
    # Get base queryset with permission filtering
    if request.user.is_staff:
        queryset = Submission.objects.all()
    else:
        queryset = Submission.objects.filter(user=request.user)

    # Filter to the specific submission
    submission_queryset = queryset.filter(uuid=uuid)

    # Check if submission exists and user has permission
    if not submission_queryset.exists():
        raise Http404("Submission not found")

    # Get submission for filename prefix
    submission = submission_queryset.first()
    if submission and submission.user:
        prefix = slugify(submission.user.username) + "_export-"
    else:
        prefix = "export-"

    return submission_queryset.export_csv(version=ExportVersion.CAAIS_1_0, filename_prefix=prefix)


require_http_methods(["GET"])


def submission_group_bulk_csv_export(request: HttpRequest, uuid: str) -> HttpResponse:
    """Generate and download a CSV for all submissions in a submission group."""
    # Get base queryset with permission filtering
    if request.user.is_staff:
        queryset = SubmissionGroup.objects.all()
    else:
        queryset = SubmissionGroup.objects.filter(created_by=request.user)

    # Filter to the specific submission group
    submission_group_queryset = queryset.filter(uuid=uuid)

    # Check if submission group exists and user has permission
    if not submission_group_queryset.exists():
        raise Http404("Submission group not found")

    # Get submission group for filename prefix
    submission_group = submission_group_queryset.first()
    if submission_group and submission_group.name:
        prefix = slugify(submission_group.name) + "_export-"
    else:
        prefix = "bulk_export-"

    # Get submissions in this group that the user has permission to see
    if request.user.is_staff:
        related_submissions = Submission.objects.filter(
            part_of_group__in=submission_group_queryset
        )
    else:
        related_submissions = Submission.objects.filter(
            part_of_group__in=submission_group_queryset, user=request.user
        )

    if not related_submissions.exists():
        raise Http404("No submissions found in this group")

    return related_submissions.export_csv(version=ExportVersion.CAAIS_1_0, filename_prefix=prefix)


class SubmissionGroupDetailView(UpdateView):
    """Handles updating and viewing details of a submission group."""

    model = SubmissionGroup
    form_class = SubmissionGroupForm
    template_name = "recordtransfer/submission_group_detail.html"
    context_object_name = "group"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.http_method_names = ["get", "post", "delete"]

    def get_object(self, queryset: Optional[QuerySet] = None) -> Submission:
        """Retrieve the SubmissionGroup object based on the UUID in the URL."""
        if queryset is None:
            queryset = self.get_queryset()

        return get_object_or_404(queryset, uuid=self.kwargs.get("uuid"))

    def get_queryset(self) -> QuerySet[SubmissionGroup]:
        """Return queryset filtered by user permissions."""
        queryset = super().get_queryset()

        if self.request.user.is_staff:
            return queryset
        else:
            return queryset.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Pass submissions associated with the group to the template."""
        context = super().get_context_data(**kwargs)
        context["js_context"] = {
            "ID_SUBMISSION_GROUP_NAME": HtmlIds.ID_SUBMISSION_GROUP_NAME,
            "ID_SUBMISSION_GROUP_DESCRIPTION": HtmlIds.ID_SUBMISSION_GROUP_DESCRIPTION,
            "PROFILE_URL": reverse("recordtransfer:user_profile"),
            # Table-related context
            "PAGINATE_QUERY_NAME": QueryParameters.PAGINATE_QUERY_NAME,
            "ID_SUBMISSION_GROUP_TABLE": HtmlIds.ID_SUBMISSION_GROUP_TABLE,
            "SUBMISSION_GROUP_TABLE_URL": reverse("recordtransfer:submission_group_table"),
            "ID_SUBMISSION_TABLE": HtmlIds.ID_SUBMISSION_TABLE,
            "SUBMISSION_TABLE_URL": f"{reverse('recordtransfer:submission_table')}?{QueryParameters.SUBMISSION_GROUP_QUERY_NAME}={self.get_object().uuid}",
        }
        return context

    def get_form_kwargs(self) -> dict[str, Any]:
        """Pass User instance to form to initialize it."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Handle valid form submission."""
        super().form_valid(form)
        response = render(
            self.request,
            self.template_name,
            self.get_context_data(),
        )
        return trigger_client_event(
            response,
            "showSuccess",
            {
                "value": gettext("Group updated"),
            },
        )

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        """Handle invalid form submission."""
        response = super().form_invalid(form)
        return trigger_client_event(
            response,
            "showError",
            {
                "value": gettext("There was an error updating the group"),
            },
        )


@require_http_methods(["GET"])
def get_user_submission_groups(request: HttpRequest) -> JsonResponse:
    """Return a JSON response containing all submission groups created by the specified user."""
    user: User = cast(User, request.user)
    submission_groups = SubmissionGroup.objects.filter(created_by=user)
    groups = [
        {"uuid": str(group.uuid), "name": group.name, "description": group.description}
        for group in submission_groups
    ]
    return JsonResponse(groups, safe=False)
