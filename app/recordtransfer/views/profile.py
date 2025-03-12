"""Views to manage user profile information and view their submission history."""

from typing import Any, cast

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext
from django.views.generic import UpdateView

from recordtransfer.constants import (
    GROUPS_PAGE,
    ID_CONFIRM_NEW_PASSWORD,
    ID_CURRENT_PASSWORD,
    ID_FIRST_NAME,
    ID_GETS_NOTIFICATION_EMAILS,
    ID_LAST_NAME,
    ID_NEW_PASSWORD,
    IN_PROGRESS_PAGE,
    SUBMISSIONS_PAGE,
)
from recordtransfer.emails import send_user_account_updated
from recordtransfer.forms import UserProfileForm
from recordtransfer.models import InProgressSubmission, Submission, SubmissionGroup


class UserProfile(UpdateView):
    """View to show two things:
    - The user's profile information
    - A list of the Submissions a user has created via transfer.
    """

    template_name = "recordtransfer/profile.html"
    paginate_by = 10
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

        # Paginate InProgressSubmission
        in_progress_submissions = InProgressSubmission.objects.filter(
            user=self.request.user
        ).order_by("-last_updated")

        in_progress_paginator = Paginator(in_progress_submissions, self.paginate_by)
        in_progress_page_number = self.request.GET.get(IN_PROGRESS_PAGE, 1)
        context["in_progress_page_obj"] = in_progress_paginator.get_page(in_progress_page_number)

        # Paginate Submission
        user_submissions = Submission.objects.filter(user=self.request.user).order_by(
            "-submission_date"
        )
        submissions_paginator = Paginator(user_submissions, self.paginate_by)
        submissions_page_number = self.request.GET.get(SUBMISSIONS_PAGE, 1)
        context["submissions_page_obj"] = submissions_paginator.get_page(submissions_page_number)

        # Paginate SubmissionGroup
        submission_groups = SubmissionGroup.objects.filter(created_by=self.request.user).order_by(
            "name"
        )
        groups_paginator = Paginator(submission_groups, self.paginate_by)
        groups_page_number = self.request.GET.get(GROUPS_PAGE, 1)
        context["groups_page_obj"] = groups_paginator.get_page(groups_page_number)

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
                # Pagination
                "IN_PROGRESS_PAGE": IN_PROGRESS_PAGE,
                "SUBMISSIONS_PAGE": SUBMISSIONS_PAGE,
                "GROUPS_PAGE": GROUPS_PAGE,
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
