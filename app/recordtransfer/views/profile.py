"""Views to manage user profile information and view their submission history."""

from typing import Any, Optional, cast

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.html import escape
from django.utils.translation import gettext
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, UpdateView
from django_htmx.http import trigger_client_event

from recordtransfer.constants import HtmlIds, QueryParameters
from recordtransfer.emails import send_user_account_updated
from recordtransfer.enums import SiteSettingKey
from recordtransfer.forms import UserProfileForm
from recordtransfer.forms.submission_group_form import SubmissionGroupForm
from recordtransfer.models import (
    InProgressSubmission,
    SiteSetting,
    Submission,
    SubmissionGroup,
    User,
)


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
                    "ID_FIRST_NAME": HtmlIds.ID_FIRST_NAME,
                    "ID_LAST_NAME": HtmlIds.ID_LAST_NAME,
                    "ID_GETS_NOTIFICATION_EMAILS": HtmlIds.ID_GETS_NOTIFICATION_EMAILS,
                    "ID_CURRENT_PASSWORD": HtmlIds.ID_CURRENT_PASSWORD,
                    "ID_NEW_PASSWORD": HtmlIds.ID_NEW_PASSWORD,
                    "ID_CONFIRM_NEW_PASSWORD": HtmlIds.ID_CONFIRM_NEW_PASSWORD,
                    # Submission group form
                    "ID_SUBMISSION_GROUP_NAME": HtmlIds.ID_SUBMISSION_GROUP_NAME,
                    # Tables
                    "PAGINATE_QUERY_NAME": QueryParameters.PAGINATE_QUERY_NAME,
                    "ID_IN_PROGRESS_SUBMISSION_TABLE": HtmlIds.ID_IN_PROGRESS_SUBMISSION_TABLE,
                    "IN_PROGRESS_SUBMISSION_TABLE_URL": reverse(
                        "recordtransfer:in_progress_submission_table"
                    ),
                    "ID_SUBMISSION_GROUP_TABLE": HtmlIds.ID_SUBMISSION_GROUP_TABLE,
                    "SUBMISSION_GROUP_TABLE_URL": reverse("recordtransfer:submission_group_table"),
                },
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
def delete_in_progress_submission(request: HttpRequest, uuid: str) -> HttpResponse:
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
            response, "showSuccess", {"value": gettext("In-progress submission deleted.")}
        )
    except Http404:
        response = HttpResponse(status=404)
        return trigger_client_event(
            response, "showError", {"value": gettext("In-progress submission not found.")}
        )
    except Exception:
        response = HttpResponse(status=500)
        return trigger_client_event(
            response, "showError", {"value": gettext("Failed to delete in-progress submission.")}
        )


def _paginated_table_view(
    request: HttpRequest,
    queryset: QuerySet,
    template_name: str,
    target_id: str,
    paginate_url: str,
    extra_context: Optional[dict[str, Any]] = None,
) -> HttpResponse:
    """Define a generic function to render paginated tables. Request must be made by HTMX, or else
    a 400 Error is returned.
    """
    if not request.htmx:
        return HttpResponse(status=400)

    paginator = Paginator(queryset, SiteSetting.get_value_int(SiteSettingKey.PAGINATE_BY))
    page_num = request.GET.get(QueryParameters.PAGINATE_QUERY_NAME, 1)

    try:
        page_num = int(page_num)
    except (TypeError, ValueError):
        page_num = 1

    if page_num < 1:
        page_num = 1
    elif page_num > paginator.num_pages:
        page_num = paginator.num_pages

    context = {
        "page": paginator.get_page(page_num),
        "page_num": page_num,
        "target_id": target_id,
        "paginate_url": paginate_url,
        **(extra_context or {}),
    }

    return render(request, template_name, context)


def submission_group_table(request: HttpRequest) -> HttpResponse:
    """Render the submission group table with pagination."""
    queryset = SubmissionGroup.objects.filter(created_by=request.user).order_by("name")
    return _paginated_table_view(
        request,
        queryset,
        "includes/submission_group_table.html",
        HtmlIds.ID_SUBMISSION_GROUP_TABLE,
        reverse("recordtransfer:submission_group_table"),
    )


def in_progress_submission_table(request: HttpRequest) -> HttpResponse:
    """Render the in-progress submission table with pagination."""
    queryset = InProgressSubmission.objects.filter(user=request.user).order_by("-last_updated")
    return _paginated_table_view(
        request,
        queryset,
        "includes/in_progress_submission_table.html",
        HtmlIds.ID_IN_PROGRESS_SUBMISSION_TABLE,
        reverse("recordtransfer:in_progress_submission_table"),
    )


def submission_table(request: HttpRequest) -> HttpResponse:
    """Render the past submission table with pagination."""
    group_uuid = request.GET.get(QueryParameters.SUBMISSION_GROUP_QUERY_NAME)
    queryset = None
    context = {}
    if group_uuid:
        queryset = Submission.objects.filter(user=request.user, part_of_group__uuid=group_uuid)
        context["IN_GROUP"] = True
    else:
        queryset = Submission.objects.filter(user=request.user)

    queryset = queryset.order_by("-submission_date")

    return _paginated_table_view(
        request,
        queryset,
        "includes/submission_table.html",
        HtmlIds.ID_SUBMISSION_TABLE,
        reverse("recordtransfer:submission_table"),
        context,
    )


class SubmissionGroupModalCreateView(CreateView):
    """Renders a modal form to create a new submission group. Handles GET requests to show the
    modal and POST requests to create the submission group. Both requests must be made by HTMX.
    """

    model = SubmissionGroup
    form_class = SubmissionGroupForm
    template_name = "includes/new_submission_group_modal.html"
    success_message = gettext("Submission group created successfully.")

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
        referer = self.request.META.get("HTTP_REFERER", "")
        response = HttpResponse(status=201)

        if reverse("recordtransfer:submit") in referer:
            return trigger_client_event(
                response,
                "submissionGroupCreated",
                {
                    "message": self.success_message,
                    "status": "success",
                    "group": {
                        "uuid": str(self.object.uuid),
                        "name": self.object.name,
                        "description": self.object.description,
                    },
                },
            )

        return trigger_client_event(response, "showSuccess", {"value": self.success_message})


@require_http_methods(["GET", "DELETE"])
def delete_submission_group(request: HttpRequest, uuid: str) -> HttpResponse:
    """Handle GET (show delete confirmation modal) and DELETE (delete submission group). Both
    requests must be made by HTMX.
    """
    if not request.htmx:
        return HttpResponse(status=400)

    try:
        submission_group = get_object_or_404(SubmissionGroup, uuid=uuid, created_by=request.user)

        if request.method == "GET":
            context = {"submission_group": submission_group}
            return render(request, "includes/delete_submission_group_modal.html", context)

        submission_group.delete()
        response = HttpResponse(status=204)
        return trigger_client_event(
            response,
            "showSuccess",
            {
                "value": gettext('Submission group "%(name)s" deleted.')
                % {"name": escape(submission_group.name)},
            },
        )
    except Http404:
        response = HttpResponse(status=404)
        return trigger_client_event(
            response, "showError", {"value": gettext("Submission group not found.")}
        )
    except Exception:
        response = HttpResponse(status=500)
        return trigger_client_event(
            response, "showError", {"value": gettext("Failed to delete submission group.")}
        )


@require_http_methods(["GET"])
def assign_submission_group_modal(request: HttpRequest, uuid: str) -> HttpResponse:
    """Display a modal that shows the submission group currently assigned to a submission and all
    available submission groups which the submission can be assigned to.

    Args:
        request (HttpRequest): The HTTP request object.
        uuid (str): The UUID of the submission.
    """
    if not request.htmx:
        return HttpResponse(status=400)

    submission = get_object_or_404(Submission, uuid=uuid, user=request.user)
    groups = SubmissionGroup.objects.filter(created_by=request.user).order_by("name")

    context = {
        "groups": groups,
        "current_group": submission.part_of_group,
        "title": submission.metadata.accession_title if submission.metadata else "",
        "js_context": {
            "groups": [
                {
                    "uuid": str(group.uuid),
                    "name": group.name,
                    "description": group.description,
                }
                for group in groups
            ],
        },
    }
    return render(request, "includes/assign_submission_group_modal.html", context)


@require_http_methods(["POST"])
def assign_submission_group(
    request: HttpRequest, submission_uuid: str, group_uuid: str
) -> HttpResponse:
    """Assign a submission to a submission group."""
    if not request.htmx:
        return HttpResponse(status=400)

    try:
        try:
            submission = Submission.objects.get(uuid=submission_uuid, user=request.user)
            group = SubmissionGroup.objects.get(uuid=group_uuid, created_by=request.user)
        except (Submission.DoesNotExist, SubmissionGroup.DoesNotExist):
            response = HttpResponse(status=404)
            return trigger_client_event(
                response, "showError", {"value": gettext("Submission or group not found")}
            )
        submission.part_of_group = group
        submission.save()
        response = HttpResponse(status=204)
        return trigger_client_event(
            response,
            "showSuccess",
            {
                "value": gettext('Submission "%(title)s" assigned to group "%(group_name)s"')
                % {
                    "title": escape(submission.metadata.accession_title)
                    if submission.metadata
                    else "",
                    "group_name": escape(group.name),
                }
            },
        )
    except Exception:
        response = HttpResponse(status=500)
        return trigger_client_event(
            response,
            "showError",
            {"value": gettext("Failed to assign submission to group")},
        )
