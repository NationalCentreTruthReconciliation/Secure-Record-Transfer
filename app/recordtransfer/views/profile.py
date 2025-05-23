"""Views to manage user profile information and view their submission history."""

from typing import Any, Optional, cast

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, UpdateView
from django_htmx.http import trigger_client_event

from recordtransfer.constants import (
    ID_CONFIRM_NEW_PASSWORD,
    ID_CURRENT_PASSWORD,
    ID_FIRST_NAME,
    ID_GETS_NOTIFICATION_EMAILS,
    ID_IN_PROGRESS_SUBMISSION_TABLE,
    ID_LAST_NAME,
    ID_NEW_PASSWORD,
    ID_SUBMISSION_GROUP_NAME,
    ID_SUBMISSION_GROUP_TABLE,
    ID_SUBMISSION_TABLE,
    PAGINATE_QUERY_NAME,
)
from recordtransfer.emails import send_user_account_updated
from recordtransfer.forms import UserProfileForm
from recordtransfer.forms.submission_group_form import SubmissionGroupForm
from recordtransfer.models import InProgressSubmission, Submission, SubmissionGroup, User


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

    def get_object(self, queryset: Optional[QuerySet] = None) -> User:
        """Get the user object for the current request."""
        return cast(User, self.request.user)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add context data for the user profile view."""
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "js_context": {
                    # User profile form
                    "ID_FIRST_NAME": ID_FIRST_NAME,
                    "ID_LAST_NAME": ID_LAST_NAME,
                    "ID_GETS_NOTIFICATION_EMAILS": ID_GETS_NOTIFICATION_EMAILS,
                    "ID_CURRENT_PASSWORD": ID_CURRENT_PASSWORD,
                    "ID_NEW_PASSWORD": ID_NEW_PASSWORD,
                    "ID_CONFIRM_NEW_PASSWORD": ID_CONFIRM_NEW_PASSWORD,
                    # Submission group form
                    "ID_SUBMISSION_GROUP_NAME": ID_SUBMISSION_GROUP_NAME,
                    # Tables
                    "PAGINATE_QUERY_NAME": PAGINATE_QUERY_NAME,
                    "ID_IN_PROGRESS_SUBMISSION_TABLE": ID_IN_PROGRESS_SUBMISSION_TABLE,
                    "IN_PROGRESS_SUBMISSION_TABLE_URL": reverse(
                        "recordtransfer:in_progress_submission_table"
                    ),
                    "ID_SUBMISSION_GROUP_TABLE": ID_SUBMISSION_GROUP_TABLE,
                    "SUBMISSION_GROUP_TABLE_URL": reverse("recordtransfer:submission_group_table"),
                },
                # Table container IDs
                "ID_SUBMISSION_TABLE": ID_SUBMISSION_TABLE,
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


@require_http_methods(["GET", "DELETE"])
def in_progress_submission(request: HttpRequest, uuid: str) -> HttpResponse:
    """Handle GET (show modal) and DELETE (delete submission) for in-progress submissions. Both
    requests must be made by HTMX, or else a 400 Error is returned.
    """
    if not request.htmx:
        return HttpResponse(status=400)

    try:
        in_progress = get_object_or_404(InProgressSubmission, uuid=uuid, user=request.user)

        if request.method == "GET":
            context = {"in_progress": in_progress}
            return render(request, "includes/delete_in_progress_submission_modal.html", context)

        # DELETE request
        in_progress.delete()
        response = HttpResponse(status=204)
        return trigger_client_event(
            response, "showSuccess", {"value": "In-progress submission deleted."}
        )
    except Http404:
        response = HttpResponse(status=404)
        return trigger_client_event(
            response, "showError", {"value": "In-progress submission not found."}
        )
    except Exception:
        response = HttpResponse(status=500)
        return trigger_client_event(
            response, "showError", {"value": "Failed to delete in-progress submission."}
        )


def _paginated_table_view(
    request: HttpRequest,
    queryset: QuerySet,
    template_name: str,
    target_id: str,
    paginate_url: str,
) -> HttpResponse:
    """Define a generic function to render paginated tables. Request must be made by HTMX, or else
    a 400 Error is returned.
    """
    if not request.htmx:
        return HttpResponse(status=400)

    paginator = Paginator(queryset, settings.PAGINATE_BY)
    page_num = request.GET.get(PAGINATE_QUERY_NAME, 1)

    try:
        page_num = int(page_num)
    except (TypeError, ValueError):
        page_num = 1

    if page_num < 1:
        page_num = 1
    elif page_num > paginator.num_pages:
        page_num = paginator.num_pages

    data = {
        "page": paginator.get_page(page_num),
        "page_num": page_num,
        "target_id": target_id,
        "paginate_url": paginate_url,
        "PAGINATE_QUERY_NAME": PAGINATE_QUERY_NAME,
    }

    return render(request, template_name, data)


def submission_group_table(request: HttpRequest) -> HttpResponse:
    """Render the submission group table with pagination."""
    queryset = SubmissionGroup.objects.filter(created_by=request.user).order_by("name")
    return _paginated_table_view(
        request,
        queryset,
        "includes/submission_group_table.html",
        ID_SUBMISSION_GROUP_TABLE,
        reverse("recordtransfer:submission_group_table"),
    )


def in_progress_submission_table(request: HttpRequest) -> HttpResponse:
    """Render the in-progress submission table with pagination."""
    queryset = InProgressSubmission.objects.filter(user=request.user).order_by("-last_updated")
    return _paginated_table_view(
        request,
        queryset,
        "includes/in_progress_submission_table.html",
        ID_IN_PROGRESS_SUBMISSION_TABLE,
        reverse("recordtransfer:in_progress_submission_table"),
    )


def submission_table(request: HttpRequest) -> HttpResponse:
    """Render the past submission table with pagination."""
    queryset = Submission.objects.filter(user=request.user).order_by("-submission_date")
    return _paginated_table_view(
        request,
        queryset,
        "includes/submission_table.html",
        ID_SUBMISSION_TABLE,
        reverse("recordtransfer:submission_table"),
    )


class SubmissionGroupModalCreateView(CreateView):
    """Renders a modal form to create a new submission group."""

    model = SubmissionGroup
    form_class = SubmissionGroupForm
    template_name = "includes/new_submission_group_modal.html"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Ensure requests are made with HTMX."""
        if not request.htmx:
            raise Http404("Page not found")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> dict[str, Any]:
        """Pass User instance to form to initialize it."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Handle valid form submission."""
        super().form_valid(form)
        response = HttpResponse(status=201)
        return trigger_client_event(
            response, "showSuccess", {"value": "Submission group created."}
        )
