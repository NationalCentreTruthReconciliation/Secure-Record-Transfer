"""Views for completed submissions, and creating and managing submission groups."""

import logging
from typing import Any, Optional

from caais.export import ExportVersion
from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.http import (
    HttpRequest,
    HttpResponse,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext
from django.views.generic import DetailView, UpdateView
from django_htmx.http import trigger_client_event

from recordtransfer.constants import HtmlIds
from recordtransfer.forms.submission_group_form import SubmissionGroupForm
from recordtransfer.models import Submission, SubmissionGroup

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


class SubmissionCsvView(DetailView):
    """Generates a CSV containing the submission and downloads that CSV."""

    model = Submission

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

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle GET request to generate and download the CSV."""
        self.get_object()
        queryset = self.get_queryset()
        prefix = slugify(queryset.first().user.username) + "_export-"
        return queryset.export_csv(version=ExportVersion.CAAIS_1_0, filename_prefix=prefix)


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


def get_user_submission_groups(request: HttpRequest, user_id: int) -> JsonResponse:
    """Retrieve the groups associated with the current user."""
    if request.user.pk != user_id and not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse(
            {"error": gettext("You do not have permission to view these groups.")},
            status=403,
        )

    submission_groups = SubmissionGroup.objects.filter(created_by=user_id)
    groups = [
        {"uuid": str(group.uuid), "name": group.name, "description": group.description}
        for group in submission_groups
    ]
    return JsonResponse(groups, safe=False)
