"""Views to manage user profile information and view their submission history."""

import logging
from typing import Any, Optional, cast

from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.html import escape
from django.utils.translation import gettext
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, UpdateView
from django_htmx.http import trigger_client_event

from recordtransfer.constants import HtmlIds, QueryParameters
from recordtransfer.emails import send_user_account_updated
from recordtransfer.forms import UserProfileForm
from recordtransfer.forms.submission_group_form import SubmissionGroupForm
from recordtransfer.forms.user_forms import ProfileContactInfoForm
from recordtransfer.models import InProgressSubmission, Submission, SubmissionGroup, User

LOGGER = logging.getLogger(__name__)


class UserProfile(View):
    """Main profile page - handles GET requests only."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render the user profile page."""
        account_info_form = UserProfileForm(instance=request.user)
        contact_info_form = ProfileContactInfoForm(instance=request.user)
        context = {
            "account_info_form": account_info_form,
            "contact_info_form": contact_info_form,
            "js_context": {
                # Account Info Form
                "ID_FIRST_NAME": HtmlIds.ID_FIRST_NAME,
                "ID_LAST_NAME": HtmlIds.ID_LAST_NAME,
                "ID_GETS_NOTIFICATION_EMAILS": HtmlIds.ID_GETS_NOTIFICATION_EMAILS,
                "ID_CURRENT_PASSWORD": HtmlIds.ID_CURRENT_PASSWORD,
                "ID_NEW_PASSWORD": HtmlIds.ID_NEW_PASSWORD,
                "ID_CONFIRM_NEW_PASSWORD": HtmlIds.ID_CONFIRM_NEW_PASSWORD,
                # Submission Group Form
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

        return render(request, "recordtransfer/profile.html", context)


class AccountInfoUpdateView(UpdateView):
    """View to update user account information such as name and notification preferences."""

    form_class = UserProfileForm
    model = User
    template_name = "includes/account_info_form.html"
    success_url = reverse_lazy("recordtransfer:user_profile")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Ensure requests are made with HTMX."""
        if not request.htmx:
            raise Http404("Page not found")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset: Optional[QuerySet] = None) -> User:
        """Get the user object for the current request."""
        return cast(User, self.request.user)

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Handle valid form submission, return updated form and trigger success event in
        response.
        """
        try:
            super().form_valid(form)
            if form.cleaned_data.get("new_password"):
                update_session_auth_hash(self.request, form.instance)
            context = self.get_context_data(form=form)
            response = self.render_to_response(context)
            send_user_account_updated.delay(self.get_object(), context)
            return trigger_client_event(
                response, "showSuccess", {"value": "Account details updated."}
            )
        except Exception:
            LOGGER.exception("Failed to update account information")
            response = HttpResponse(status=500)
            return trigger_client_event(
                response, "showError", {"value": gettext("Failed to update account information.")}
            )

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        """Handle invalid form submission."""
        return super().form_invalid(form)


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

    paginator = Paginator(queryset, settings.PAGINATE_BY)
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
