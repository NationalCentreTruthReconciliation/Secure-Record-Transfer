"""Views to manage user profile information and view their submission history."""

import logging
from typing import Any, Optional, cast

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, DateTimeField, ExpressionWrapper, F, QuerySet
from django.forms import BaseModelForm
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, UpdateView
from django_htmx.http import trigger_client_event

from recordtransfer.constants import FormFieldNames, HtmlIds, OtherValues, QueryParameters
from recordtransfer.enums import SiteSettingKey
from recordtransfer.forms import (
    SubmissionGroupForm,
    UserAccountInfoForm,
    UserContactInfoForm,
)
from recordtransfer.models import (
    InProgressSubmission,
    SiteSetting,
    Submission,
    SubmissionGroup,
    User,
)

LOGGER = logging.getLogger(__name__)


class UserProfile(View):
    """Main profile page - handles GET requests only."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render the user profile page."""
        user = cast(User, request.user)
        context = {
            "account_info_form": UserAccountInfoForm(instance=user),
            "contact_info_form": UserContactInfoForm(instance=user),
            "js_context": {
                # Account Info Form
                "ID_FIRST_NAME": HtmlIds.ID_FIRST_NAME,
                "ID_LAST_NAME": HtmlIds.ID_LAST_NAME,
                "ID_GETS_NOTIFICATION_EMAILS": HtmlIds.ID_GETS_NOTIFICATION_EMAILS,
                # Contact Info Form
                "id_province_or_state": HtmlIds.ID_CONTACT_INFO_PROVINCE_OR_STATE,
                "id_other_province_or_state": HtmlIds.ID_CONTACT_INFO_OTHER_PROVINCE_OR_STATE,
                "other_province_or_state_value": OtherValues.PROVINCE_OR_STATE,
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
                "ID_SUBMISSION_TABLE": HtmlIds.ID_SUBMISSION_TABLE,
                "SUBMISSION_TABLE_URL": reverse("recordtransfer:submission_table"),
            },
        }

        return render(request, "recordtransfer/profile.html", context)


class BaseUserProfileUpdateView(UpdateView):
    """Base view for updating user profile information."""

    model = User
    success_url = reverse_lazy("recordtransfer:user_profile")
    update_success_message = _("Updated successfully")
    update_error_message = _("Could not update")

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
            context = self.get_context_data(form=form)
            response = self.render_to_response(context)
            return trigger_client_event(
                response, "showSuccess", {"value": self.update_success_message}
            )
        except Exception:
            LOGGER.exception("Failed to update user information for user %s", self.request.user.id)
            response = HttpResponse(status=500)
            return trigger_client_event(
                response, "showError", {"value": self.update_error_message}
            )

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        """Handle invalid form submission."""
        super().form_invalid(form)
        context = self.get_context_data(form=form)
        response = self.render_to_response(context)
        return trigger_client_event(
            response, "showError", {"value": _("Please correct the errors below.")}
        )


class AccountInfoUpdateView(BaseUserProfileUpdateView):
    """View to update user account information such as name and notification preferences."""

    form_class = UserAccountInfoForm
    template_name = "includes/account_info_form.html"
    update_success_message = _("Account details updated.")
    update_error_message = _("Failed to update account information.")


class ContactInfoUpdateView(BaseUserProfileUpdateView):
    """View to update user contact information such as email and phone number."""

    form_class = UserContactInfoForm
    template_name = "includes/contact_info_form.html"
    update_success_message = _("Contact information updated.")
    update_error_message = _("Failed to update contact information.")


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
            response, "showSuccess", {"value": _("In-progress submission deleted.")}
        )
    except Http404:
        response = HttpResponse(status=404)
        return trigger_client_event(
            response, "showError", {"value": _("In-progress submission not found.")}
        )
    except Exception:
        response = HttpResponse(status=500)
        return trigger_client_event(
            response, "showError", {"value": _("Failed to delete in-progress submission.")}
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
    """Render the submission group table with pagination and sorting."""
    sort_options = {
        "name": _("Group Name"),
        "description": _("Group Description"),
        "submissions": _("Submissions in Group"),
    }

    allowed_sorts = {
        "name": "name",
        "description": "description",
        "submissions": "submission_count",
    }
    default_sort = "name"
    default_direction = "asc"

    sort = request.GET.get("sort", default_sort)
    if sort not in allowed_sorts:
        sort = default_sort

    direction = request.GET.get("direction", default_direction)
    if direction not in {"asc", "desc"}:
        direction = default_direction

    order_field = allowed_sorts[sort]
    if direction == "desc":
        order_field = f"-{order_field}"

    queryset = (
        SubmissionGroup.objects.filter(created_by=request.user)
        .annotate(submission_count=Count("submission"))
        .order_by(order_field)
    )
    return _paginated_table_view(
        request,
        queryset,
        "includes/submission_group_table.html",
        HtmlIds.ID_SUBMISSION_GROUP_TABLE,
        reverse("recordtransfer:submission_group_table"),
        extra_context={
            "current_sort": sort,
            "current_direction": direction,
            "sort_options": sort_options,
            "target_id": HtmlIds.ID_SUBMISSION_GROUP_TABLE,
        },
    )


def in_progress_submission_table(request: HttpRequest) -> HttpResponse:
    """Render the in-progress submission table with pagination."""
    expire_minutes = settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES

    if expire_minutes != -1:
        sort_options = {
            "last_updated": _("Last Updated"),
            "submission_title": _("Submission Title"),
            "expires_at": _("Expires At"),
        }

        allowed_sorts = {
            "last_updated": "last_updated",
            "submission_title": "title",
            "expires_at": "expires_at",
        }

        queryset = InProgressSubmission.objects.filter(user=request.user).annotate(
            expires_at=ExpressionWrapper(
                F("upload_session__last_upload_interaction_time")
                + timezone.timedelta(minutes=expire_minutes),
                output_field=DateTimeField(),
            )
        )
    else:
        sort_options = {
            "last_updated": _("Last Updated"),
            "submission_title": _("Submission Title"),
        }

        allowed_sorts = {
            "last_updated": "last_updated",
            "submission_title": "title",
        }

        queryset = InProgressSubmission.objects.filter(user=request.user)

    default_sort = "last_updated"
    default_direction = "desc"

    sort = request.GET.get("sort", default_sort)
    if sort not in allowed_sorts:
        sort = default_sort

    direction = request.GET.get("direction", default_direction)
    if direction not in {"asc", "desc"}:
        direction = default_direction

    order_field = allowed_sorts[sort]
    if direction == "desc":
        order_field = f"-{order_field}"

    queryset = queryset.order_by(order_field)
    return _paginated_table_view(
        request,
        queryset,
        "includes/in_progress_submission_table.html",
        HtmlIds.ID_IN_PROGRESS_SUBMISSION_TABLE,
        reverse("recordtransfer:in_progress_submission_table"),
        extra_context={
            "current_sort": sort,
            "current_direction": direction,
            "sort_options": sort_options,
            "target_id": HtmlIds.ID_IN_PROGRESS_SUBMISSION_TABLE,
        },
    )


def submission_table(request: HttpRequest) -> HttpResponse:
    """Render the past submission table with pagination and sorting,
    optionally filtered by group.
    """
    sort_options = {
        "submission_date": _("Date Submitted"),
        "submission_title": _("Submission Title"),
        "submission_group": _("Submission Group"),
    }
    allowed_sorts = {
        "submission_date": "submission_date",
        "submission_title": "metadata__accession_title",
        "submission_group": "part_of_group",
    }
    default_sort = "submission_date"
    default_direction = "desc"

    sort = request.GET.get("sort", default_sort)
    if sort not in allowed_sorts:
        sort = default_sort

    direction = request.GET.get("direction", default_direction)
    if direction not in {"asc", "desc"}:
        direction = default_direction

    order_field = allowed_sorts[sort]
    if direction == "desc":
        order_field = f"-{order_field}"

    group_uuid = request.GET.get(QueryParameters.SUBMISSION_GROUP_QUERY_NAME)
    context = {
        "current_sort": sort,
        "current_direction": direction,
        "sort_options": sort_options,
        "target_id": HtmlIds.ID_SUBMISSION_TABLE,
    }
    if group_uuid:
        queryset = Submission.objects.filter(user=request.user, part_of_group__uuid=group_uuid)
        context["IN_GROUP"] = True
    else:
        queryset = Submission.objects.filter(user=request.user)

    queryset = queryset.order_by(order_field)

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
    success_message = _("Submission group created successfully.")

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
                "value": _('Submission group "%(name)s" deleted.')
                % {"name": escape(submission_group.name)},
            },
        )
    except Http404:
        response = HttpResponse(status=404)
        return trigger_client_event(
            response, "showError", {"value": _("Submission group not found.")}
        )
    except Exception:
        response = HttpResponse(status=500)
        return trigger_client_event(
            response, "showError", {"value": _("Failed to delete submission group.")}
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
        "submission_title": submission.metadata.accession_title if submission.metadata else "",
        "submission_uuid": submission.uuid,
    }
    return render(request, "includes/assign_submission_group_modal.html", context)


@require_http_methods(["POST"])
def assign_submission_group(request: HttpRequest) -> HttpResponse:
    """Assign a submission to a submission group or unassign it."""
    if not request.htmx:
        return HttpResponse(status=400)

    try:
        submission_uuid = request.POST.get(FormFieldNames.SUBMISSION_UUID)
        group_uuid = request.POST.get(FormFieldNames.GROUP_UUID)
        unassign = FormFieldNames.UNASSIGN_GROUP in request.POST

        if not submission_uuid:
            raise ValueError("Submission UUID is required.")
        if not group_uuid and not unassign:
            raise ValueError("Group UUID is required.")

        try:
            submission = Submission.objects.get(uuid=submission_uuid, user=request.user)
            group = None
            # We only need the group if we are assigning to it
            if not unassign:
                group = SubmissionGroup.objects.get(uuid=group_uuid, created_by=request.user)
        except (Submission.DoesNotExist, SubmissionGroup.DoesNotExist):
            response = HttpResponse(status=404)
            return trigger_client_event(
                response, "showError", {"value": _("Submission or group not found")}
            )

        submission_title = (
            escape(submission.metadata.accession_title) if submission.metadata else ""
        )

        if unassign:
            return _handle_unassign_submission(submission, submission_title)

        assert group is not None, "Group should not be None in assign case"
        return _handle_assign_submission(submission, group, submission_title)

    except Exception:
        response = HttpResponse(status=500)
        return trigger_client_event(
            response,
            "showError",
            {"value": _("Failed to assign submission to group")},
        )


def _handle_unassign_submission(submission: Submission, submission_title: str) -> HttpResponse:
    """Handle unassigning a submission from its group."""
    original_group = submission.part_of_group

    # Early return for case where submission is not part of any group
    if not original_group:
        response = HttpResponse(status=400)
        return trigger_client_event(
            response,
            "showError",
            {
                "value": _('Submission "%(title)s" is not assigned to any group')
                % {"title": submission_title}
            },
        )

    submission.part_of_group = None
    submission.save()

    success_message = _('Submission "%(title)s" unassigned from group "%(group_name)s"') % {
        "title": submission_title,
        "group_name": escape(original_group.name),
    }

    response = HttpResponse(status=204)
    return trigger_client_event(response, "showSuccess", {"value": success_message})


def _handle_assign_submission(
    submission: Submission, group: SubmissionGroup, submission_title: str
) -> HttpResponse:
    """Handle assigning a submission to a group."""
    submission.part_of_group = group
    submission.save()

    success_message = _('Submission "%(title)s" assigned to group "%(group_name)s"') % {
        "title": submission_title,
        "group_name": escape(group.name) if group else "",
    }

    response = HttpResponse(status=204)
    return trigger_client_event(response, "showSuccess", {"value": success_message})
