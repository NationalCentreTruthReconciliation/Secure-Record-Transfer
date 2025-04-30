"""Views to manage user profile information and view their submission history."""

from typing import Any, cast

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.forms import BaseModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext
from django.views.generic import UpdateView

from recordtransfer.constants import (
    ID_CONFIRM_NEW_PASSWORD,
    ID_CURRENT_PASSWORD,
    ID_FIRST_NAME,
    ID_GETS_NOTIFICATION_EMAILS,
    ID_IN_PROGRESS_SUBMISSION_TABLE,
    ID_LAST_NAME,
    ID_NEW_PASSWORD,
    ID_SUBMISSION_GROUP_TABLE,
    ID_SUBMISSION_TABLE,
    PAGINATE_BY,
    PAGINATE_QUERY_NAME,
)
from recordtransfer.emails import send_user_account_updated
from recordtransfer.forms import UserProfileForm
from recordtransfer.models import InProgressSubmission, Submission, SubmissionGroup


class UserProfile(UpdateView):
    """View to show two things:
    - The user's profile information
    - A list of the Submissions a user has made.
    """

    template_name = "recordtransfer/profile.html"
    form_class = UserProfileForm
    success_url = reverse_lazy("recordtransfer:user_profile")
    success_message = gettext("Preferences updated")
    password_change_success_message = gettext("Password updated")
    error_message = gettext("There was an error updating your preferences. Please try again.")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add context data for the user profile view."""
        context = super().get_context_data(**kwargs)
        context.update(
            {
                # Form field element IDs
                "js_context": {
                    "ID_FIRST_NAME": ID_FIRST_NAME,
                    "ID_LAST_NAME": ID_LAST_NAME,
                    "ID_GETS_NOTIFICATION_EMAILS": ID_GETS_NOTIFICATION_EMAILS,
                    "ID_CURRENT_PASSWORD": ID_CURRENT_PASSWORD,
                    "ID_NEW_PASSWORD": ID_NEW_PASSWORD,
                    "ID_CONFIRM_NEW_PASSWORD": ID_CONFIRM_NEW_PASSWORD,
                },
                # Table container IDs
                "ID_SUBMISSION_GROUP_TABLE": ID_SUBMISSION_GROUP_TABLE,
                "ID_IN_PROGRESS_SUBMISSION_TABLE": ID_IN_PROGRESS_SUBMISSION_TABLE,
            }
        )

        return context

    def get_form_kwargs(self) -> dict[str, Any]:
        """Pass User instance to form to initialize it."""
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_object()
        return kwargs

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Handle valid form submission."""
        response = super().form_valid(form)
        message = self.success_message
        if form.cleaned_data.get("new_password"):
            update_session_auth_hash(self.request, form.instance)
            message = self.password_change_success_message

            context = {
                "subject": gettext("Password updated"),
                "changed_item": gettext("password"),
                "changed_status": gettext("updated"),
            }
            send_user_account_updated.delay(self.get_object(), context)

        messages.success(self.request, message)
        return response

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        """Handle invalid form submission."""
        messages.error(
            self.request,
            self.error_message,
        )
        profile_form = cast(UserProfileForm, form)
        profile_form.reset_form()
        return super().form_invalid(profile_form)


def submission_group_table(request: HttpRequest) -> HttpResponse:
    """Render the submission group table with pagination."""
    if not request.htmx:
        return HttpResponse(status=400)

    submission_groups = SubmissionGroup.objects.filter(created_by=request.user).order_by("name")
    paginator = Paginator(submission_groups, PAGINATE_BY)
    page_num = request.GET.get(PAGINATE_QUERY_NAME, 1)

    data = {
        "page": paginator.get_page(page_num),
        "page_num": page_num,
        "target_id": ID_SUBMISSION_GROUP_TABLE,
        "paginate_url": reverse("recordtransfer:submission_group_table"),
        "PAGINATE_QUERY_NAME": PAGINATE_QUERY_NAME,
    }

    return render(request, "includes/submission_group_table.html", data)


def in_progress_submission_table(request: HttpRequest) -> HttpResponse:
    """Render the in-progress submission table with pagination."""
    if not request.htmx:
        return HttpResponse(status=400)

    in_progress_submissions = InProgressSubmission.objects.filter(user=request.user).order_by(
        "-last_updated"
    )
    paginator = Paginator(in_progress_submissions, PAGINATE_BY)
    page_num = request.GET.get(PAGINATE_QUERY_NAME, 1)

    data = {
        "page": paginator.get_page(page_num),
        "page_num": page_num,
        "target_id": ID_IN_PROGRESS_SUBMISSION_TABLE,
        "paginate_url": reverse("recordtransfer:in_progress_submission_table"),
        "PAGINATE_QUERY_NAME": PAGINATE_QUERY_NAME,
    }

    return render(request, "includes/in_progress_submission_table.html", data)


def submission_table(request: HttpRequest) -> HttpResponse:
    """Render the past submission table with pagination."""
    if not request.htmx:
        return HttpResponse(status=400)

    submissions = Submission.objects.filter(user=request.user).order_by("-submission_date")
    paginator = Paginator(submissions, PAGINATE_BY)
    page_num = request.GET.get(PAGINATE_QUERY_NAME, 1)

    data = {
        "page": paginator.get_page(page_num),
        "page_num": page_num,
        "target_id": ID_SUBMISSION_TABLE,
        "paginate_url": reverse("recordtransfer:submission_table"),
        "PAGINATE_QUERY_NAME": PAGINATE_QUERY_NAME,
    }

    return render(request, "includes/submission_table.html", data)
