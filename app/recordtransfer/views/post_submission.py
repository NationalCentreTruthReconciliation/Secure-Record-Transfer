"""Views for completed submissions, and creating and managing submission groups."""

import logging
from typing import Any

from caais.export import ExportVersion
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.forms import BaseModelForm
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext
from django.views.generic import CreateView, DetailView, UpdateView, View

from recordtransfer.constants import ID_SUBMISSION_GROUP_DESCRIPTION, ID_SUBMISSION_GROUP_NAME
from recordtransfer.forms.submission_group_form import SubmissionGroupForm
from recordtransfer.models import Submission, SubmissionGroup

LOGGER = logging.getLogger(__name__)


class SubmissionDetail(UserPassesTestMixin, DetailView):
    """Generates a report for a given submission."""

    model = Submission
    template_name = "recordtransfer/submission_detail.html"
    context_object_name = "submission"

    def get_object(self, queryset=None) -> Submission:
        """Retrieve the Submission object based on the UUID in the URL."""
        return get_object_or_404(Submission, uuid=self.kwargs.get("uuid"))

    def test_func(self) -> bool:
        """Check if the user is the creator of the submission group or is a staff member."""
        return self.request.user.is_staff or self.get_object().user == self.request.user

    def handle_no_permission(self):
        """Override to return 404 instead of 403. This is to prevent users from knowing that the
        submission exists if they do not have permission to view it.
        """
        raise Http404("Page not found")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["current_date"] = timezone.now()
        context["metadata"] = context["submission"].metadata
        return context


class SubmissionCsv(UserPassesTestMixin, View):
    """Generates a CSV containing the submission and downloads that CSV."""

    def get_object(self):
        self.get_queryset().first()

    def get_queryset(self):
        uuid = self.kwargs["uuid"]
        try:
            return Submission.objects.filter(uuid=str(uuid))
        except Submission.DoesNotExist:
            raise Http404

    def test_func(self):
        submission = self.get_object()
        # Check if the user is the creator of the submission or is a staff member
        return self.request.user.is_staff or submission.user == self.request.user

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        prefix = slugify(queryset.first().user.username) + "_export-"
        return queryset.export_csv(version=ExportVersion.CAAIS_1_0, filename_prefix=prefix)


class SubmissionGroupDetailView(UserPassesTestMixin, UpdateView):
    """Displays the associated submissions for a given submission group, and allows modification
    of submission group details.
    """

    model = SubmissionGroup
    form_class = SubmissionGroupForm
    template_name = "recordtransfer/submission_group_show_create.html"
    context_object_name = "group"
    success_message = gettext("Group updated")
    error_message = gettext("There was an error updating the group")

    def get_object(self):
        return get_object_or_404(SubmissionGroup, uuid=self.kwargs.get("uuid"))

    def test_func(self):
        """Check if the user is the creator of the submission group or is a staff member."""
        return self.request.user.is_staff or self.get_object().created_by == self.request.user

    def handle_no_permission(self):
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
            LOGGER.error(
                "Error deleting submission group %s: %s", self.get_object().uuid, str(e)
            )

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


class SubmissionGroupCreateView(UserPassesTestMixin, CreateView):
    """Creates a new submission group."""

    model = SubmissionGroup
    form_class = SubmissionGroupForm
    template_name = "recordtransfer/submission_group_show_create.html"
    success_message = gettext("Group created")
    error_message = gettext("There was an error creating the group")

    def test_func(self):
        """Check if the user is authenticated."""
        return self.request.user.is_authenticated

    def handle_no_permission(self) -> HttpResponseForbidden:
        return HttpResponseForbidden("You do not have permission to access this page.")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
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
        response = super().form_valid(form)
        referer = self.request.headers.get("referer", "")
        if "submission/" in referer:
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
        messages.success(self.request, self.success_message)
        return response

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        """Handle invalid form submission."""
        referer = self.request.headers.get("referer", "")
        error_message = next(iter(form.errors.values()))[0]
        if "submission/" in referer:
            return JsonResponse({"message": error_message, "status": "error"}, status=400)
        messages.error(
            self.request,
            self.error_message,
        )
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
