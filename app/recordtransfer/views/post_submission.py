"""Views for completed submissions, and creating and managing submission groups."""

import logging
from typing import Any, Optional

from caais.export import ExportVersion
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext
from django.views.generic import CreateView, DetailView, UpdateView, View
from django_htmx.http import trigger_client_event

from recordtransfer.constants import ID_SUBMISSION_GROUP_DESCRIPTION, ID_SUBMISSION_GROUP_NAME
from recordtransfer.forms.submission_group_form import SubmissionGroupForm
from recordtransfer.models import Submission, SubmissionGroup

LOGGER = logging.getLogger(__name__)


class SubmissionDetail(UserPassesTestMixin, DetailView):
    """Generates a report for a given submission."""

    model = Submission
    template_name = "recordtransfer/submission_detail.html"
    context_object_name = "submission"

    def get_object(self, queryset: Optional[QuerySet] = None) -> Submission:
        """Retrieve the Submission object based on the UUID in the URL."""
        return get_object_or_404(Submission, uuid=self.kwargs.get("uuid"))

    def test_func(self) -> bool:
        """Check if the user is the creator of the submission group or is a staff member."""
        return self.request.user.is_staff or self.get_object().user == self.request.user

    def handle_no_permission(self) -> HttpResponseRedirect:
        """Override to return 404 instead of 403. This is to prevent users from knowing that the
        submission exists if they do not have permission to view it.
        """
        raise Http404("Page not found")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Pass context variables to the template."""
        context = super().get_context_data(**kwargs)
        context["current_date"] = timezone.now()
        context["metadata"] = context["submission"].metadata
        return context


class SubmissionCsv(UserPassesTestMixin, View):
    """Generates a CSV containing the submission and downloads that CSV."""

    def get_object(self) -> Submission:
        """Retrieve the Submission object based on the UUID in the URL."""
        submission = self.get_queryset().first()
        if submission is None:
            raise Http404("Submission not found")
        return submission

    def get_queryset(self) -> QuerySet[Submission]:
        """Retrieve a queryset of submissions based on the UUID in the URL. There should only be
        one submission in the queryset.
        """
        uuid = self.kwargs["uuid"]
        queryset = Submission.objects.filter(uuid=str(uuid))
        return queryset

    def test_func(self) -> bool:
        """Prevent users from accessing the CSV download if they do not have the correct
        permissions.
        """
        submission = self.get_object()
        # Check if the user is the creator of the submission or is a staff member
        return self.request.user.is_staff or submission.user == self.request.user

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle GET request to generate and download the CSV."""
        queryset = self.get_queryset()
        prefix = slugify(queryset.first().user.username) + "_export-"
        return queryset.export_csv(version=ExportVersion.CAAIS_1_0, filename_prefix=prefix)


class SubmissionGroupDetailView(UserPassesTestMixin, UpdateView):
    """Displays the associated submissions for a given submission group, and allows modification
    of submission group details.
    """

    model = SubmissionGroup
    form_class = SubmissionGroupForm
    template_name = "recordtransfer/submission_group_detail.html"
    context_object_name = "group"
    success_message = gettext("Group updated")
    error_message = gettext("There was an error updating the group")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.http_method_names = ["get", "post", "delete"]

    def get_object(self, queryset: Optional[QuerySet] = None) -> SubmissionGroup:
        """Retrieve the SubmissionGroup object based on the UUID in the URL."""
        return get_object_or_404(SubmissionGroup, uuid=self.kwargs.get("uuid"))

    def test_func(self) -> bool:
        """Check if the user is the creator of the submission group or is a staff member."""
        return self.request.user.is_staff or self.get_object().created_by == self.request.user

    def handle_no_permission(self) -> HttpResponseRedirect:
        """Override to return 404 instead of 403. This is to prevent users from knowing that the
        group exists if they do not have permission to view it.
        """
        raise Http404("Page not found")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Pass submissions associated with the group to the template."""
        context = super().get_context_data(**kwargs)
        context["submissions"] = Submission.objects.filter(part_of_group=self.get_object())
        context["IS_NEW"] = False
        context["js_context"] = {
            "id_submission_group_name": ID_SUBMISSION_GROUP_NAME,
            "id_submission_group_description": ID_SUBMISSION_GROUP_DESCRIPTION,
            "DELETE_URL": reverse(
                "recordtransfer:submission_group_detail",
                kwargs={"uuid": self.get_object().uuid},
            ),
        }
        return context

    def delete(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle DELETE request to delete the submission group."""
        try:
            group = self.get_object()
            group.delete()
            messages.success(request, gettext("Group deleted"))
        except Exception as e:
            messages.error(request, gettext("There was an error deleting the group"))
            LOGGER.error("Error deleting submission group %s: %s", self.get_object().uuid, str(e))

        return redirect("recordtransfer:user_profile")

    def get_form_kwargs(self) -> dict[str, Any]:
        """Pass User instance to form to initialize it."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Handle valid form submission."""
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        """Handle invalid form submission."""
        messages.error(
            self.request,
            self.error_message,
        )
        return super().form_invalid(form)

    def get_success_url(self) -> str:
        """Redirect back to the same page after updating the group."""
        return self.request.path


class SubmissionGroupCreateView(CreateView):
    """Creates a new submission group."""

    model = SubmissionGroup
    form_class = SubmissionGroupForm
    template_name = "recordtransfer/submission_group_detail.html"
    success_message = gettext("Group created")

    def get_template_names(self) -> list[str]:
        """Dynamically select template based on referrer."""
        referrer = self.request.META.get("HTTP_REFERER", "")
        if reverse("recordtransfer:user_profile") in referrer:
            return ["includes/new_submission_group_modal.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Pass context variables to the template."""
        context = super().get_context_data(**kwargs)
        context["IS_NEW"] = True
        context["ID_SUBMISSION_GROUP_NAME"] = ID_SUBMISSION_GROUP_NAME
        context["ID_SUBMISSION_GROUP_DESCRIPTION"] = ID_SUBMISSION_GROUP_DESCRIPTION
        context["MODAL_MODE"] = False
        return context

    def get_form_kwargs(self) -> dict[str, Any]:
        """Pass User instance to form to initialize it."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Handle valid form submission."""
        super().form_valid(form)
        referer = self.request.headers.get("referer", "")
        if reverse("recordtransfer:submit") in referer:
            return JsonResponse(
                {
                    "message": self.success_message,
                    "status": "success",
                    "group": {
                        "uuid": str(self.object.uuid),
                        "name": self.object.name,
                        "description": self.object.description,
                    },
                },
                status=200,
            )
        response = HttpResponse(status=201)
        return trigger_client_event(
            response, "showSuccess", {"value": "Submission group created."}
        )

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        """Handle invalid form submission."""
        referer = self.request.headers.get("referer", "")
        error_message = next(iter(form.errors.values()))[0]
        if reverse("recordtransfer:submit") in referer:
            return JsonResponse({"message": error_message, "status": "error"}, status=400)
        return super().form_invalid(form)


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
