"""Views for the submission form and submission process, responsible for creating, saving, and
deleting in-progress submissions, as well as handling the final submission.
"""

import dataclasses
import logging
import pickle
import re
from typing import Any, ClassVar, Optional, OrderedDict, Union, cast

from caais.models import RightsType, SourceRole, SourceType
from django.conf import settings
from django.contrib import messages
from django.forms import (
    BaseForm,
    BaseFormSet,
    BaseInlineFormSet,
    BaseModelFormSet,
    ModelForm,
    formset_factory,
)
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    QueryDict,
)
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext
from django.views.generic import TemplateView
from django_htmx.http import HttpResponseClientRedirect, trigger_client_event
from formtools.wizard.views import SessionWizardView

from recordtransfer import forms
from recordtransfer.caais import map_form_to_metadata
from recordtransfer.constants import (
    HeaderNames,
    HtmlIds,
    OtherValues,
    QueryParameters,
)
from recordtransfer.emails import (
    send_submission_creation_failure,
    send_submission_creation_success,
    send_thank_you_for_your_submission,
    send_your_submission_did_not_go_through,
)
from recordtransfer.enums import SubmissionStep
from recordtransfer.models import (
    InProgressSubmission,
    Submission,
    UploadSession,
    User,
)

LOGGER = logging.getLogger(__name__)


class SubmissionSent(TemplateView):
    """The page a user sees when they finish a submission."""

    template_name = "recordtransfer/submission_sent.html"


class InProgressSubmissionExpired(TemplateView):
    """The page a user sees when they try to access an expired submission."""

    template_name = "recordtransfer/in_progress_submission_expired.html"


class SubmissionFormWizard(SessionWizardView):
    """A multi-page form for collecting user metadata and uploading files. Uses a form wizard. For
    more info, visit this link: https://django-formtools.readthedocs.io/en/latest/wizard.html.
    """

    @dataclasses.dataclass
    class SubmissionStepMeta:
        """Metadata for each submission step, including the template to render, title, form class,
        and an optional info message to display on the page.
        """

        template: str
        title: str
        form: type[Union[forms.SubmissionForm, BaseFormSet]]
        info_message: Optional[str] = None

    _TEMPLATES: ClassVar[dict[SubmissionStep, SubmissionStepMeta]] = {
        SubmissionStep.ACCEPT_LEGAL: SubmissionStepMeta(
            template="recordtransfer/submission_form_legal.html",
            title=gettext("Legal Agreement"),
            form=forms.AcceptLegal,
        ),
        SubmissionStep.CONTACT_INFO: SubmissionStepMeta(
            template="recordtransfer/submission_form_standard.html",
            title=gettext("Contact Information"),
            form=forms.ContactInfoForm,
            info_message=gettext(
                "Enter your contact information in case you need to be contacted by one of our "
                "archivists regarding your submission"
            ),
        ),
        SubmissionStep.SOURCE_INFO: SubmissionStepMeta(
            template="recordtransfer/submission_form_sourceinfo.html",
            title=gettext("Record Source Information (Optional)"),
            form=forms.SourceInfoForm,
            info_message=gettext(
                "Are you submitting records on behalf of another person or organization? Select Yes to enter information about them."
            ),
        ),
        SubmissionStep.RECORD_DESCRIPTION: SubmissionStepMeta(
            template="recordtransfer/submission_form_standard.html",
            title=gettext("Record Description"),
            form=forms.RecordDescriptionForm
            if settings.FILE_UPLOAD_ENABLED
            else forms.ExtendedRecordDescriptionForm,
            info_message=gettext("Provide a brief description of the records you're submitting"),
        ),
        SubmissionStep.RIGHTS: SubmissionStepMeta(
            template="recordtransfer/submission_form_formset.html",
            title=gettext("Record Rights and Restrictions (Optional)"),
            form=formset_factory(forms.RightsForm, formset=forms.RightsFormSet, extra=1),
            info_message=gettext(
                "Depending on the records you are submitting, there may be specific rights that govern "
                "the access of your records. <br> <br>"
                " Need help understanding rights types? "
                '<a class="non-nav-link link-primary font-semibold underline" target="_blank" href="/help#rights-types">View our guide</a> for detailed explanations.'
            ),
        ),
        SubmissionStep.OTHER_IDENTIFIERS: SubmissionStepMeta(
            template="recordtransfer/submission_form_formset.html",
            title=gettext("Identifiers (Optional)"),
            form=formset_factory(
                forms.OtherIdentifiersForm,
                formset=forms.OtherIdentifiersFormSet,
                extra=1,
            ),
            info_message=gettext(
                "If you have any identifiers associated with these records, such as reference numbers, codes, or other unique IDs, you may enter them here. "
                "<b> This step is optional</b>. If you do not have any identifiers associated with the records, you may proceed to the next step."
            ),
        ),
        SubmissionStep.GROUP_SUBMISSION: SubmissionStepMeta(
            template="recordtransfer/submission_form_groupsubmission.html",
            title=gettext("Assign Submission to Group (Optional)"),
            form=forms.GroupSubmissionForm,
        ),
        **(
            {
                SubmissionStep.UPLOAD_FILES: SubmissionStepMeta(
                    template="recordtransfer/submission_form_uploadfiles.html",
                    title=gettext("Upload Files"),
                    form=forms.UploadFilesForm,
                    info_message=gettext(
                        "Add any final notes you would like to add, and upload your files"
                    ),
                )
            }
            if settings.FILE_UPLOAD_ENABLED
            else {
                SubmissionStep.FINAL_NOTES: SubmissionStepMeta(
                    template="recordtransfer/submission_form_standard.html",
                    title=gettext("Final Notes"),
                    form=forms.FinalStepFormNoUpload,
                    info_message=gettext(
                        "Add any final notes that may not have fit in previous steps"
                    ),
                )
            }
        ),
        SubmissionStep.REVIEW: SubmissionStepMeta(
            template="recordtransfer/submission_form_review.html",
            title=gettext("Review"),
            form=forms.ReviewForm,
            info_message=gettext("Review the information you've entered before submitting"),
        ),
    }

    form_list: ClassVar[list[tuple]] = [
        (step.value, step_metadata.form) for step, step_metadata in _TEMPLATES.items()
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.submission_group_uuid = None
        self.in_progress_submission = None
        self.in_progress_uuid = None

    @property
    def current_step(self) -> SubmissionStep:
        """Returns the current step as a SubmissionStep enum value."""
        current = self.steps.current
        try:
            return SubmissionStep(current)  # Converts string to enum
        except ValueError as exc:
            LOGGER.error("Invalid step name: %s", current)
            raise Http404("Invalid step name") from exc

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Dispatch the request to the appropriate handler method."""
        self.in_progress_uuid = request.GET.get("resume")

        if not self.in_progress_uuid:
            self.submission_group_uuid = request.GET.get(
                QueryParameters.SUBMISSION_GROUP_QUERY_NAME
            )
            return super().dispatch(request, *args, **kwargs)

        self.in_progress_submission = InProgressSubmission.objects.filter(
            user=request.user, uuid=self.in_progress_uuid
        ).first()

        # Redirect user to a fresh submission form if the in-progress submission is not found
        if not self.in_progress_submission:
            return redirect("recordtransfer:submit")

        # Check if associated upload session is expired or not
        if self.in_progress_submission.upload_session_expired:
            return redirect("recordtransfer:in_progress_submission_expired")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle GET request to load a submission."""
        if self.in_progress_submission:
            self.load_form_data()
            return self.render(self.get_form())

        return super().get(request, *args, **kwargs)

    def load_form_data(self) -> None:
        """Load form data from an InProgressSubmission instance."""
        if not self.in_progress_submission:
            raise ValueError("No in-progress submission to load")

        self.storage.data = pickle.loads(self.in_progress_submission.step_data)["past"]
        self.storage.current_step = self.in_progress_submission.current_step

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle POST request to save a submission."""
        # User is not saving the form, so continue with the normal form submission
        if not request.POST.get("save_form_step", None):
            return super().post(request, *args, **kwargs)

        try:
            self.save_form_data(request)
            message = gettext("Submission saved successfully.")
            if (
                expires_at := self.in_progress_submission.upload_session_expires_at
                if self.in_progress_submission
                else None
            ):
                expiry_message = gettext(
                    "This submission will expire on %(date)s. Please be sure to complete your "
                    "submission before then."
                ) % {"date": timezone.localtime(expires_at).strftime(r"%a %b %-d, %Y @ %H:%M")}
                message = message + " " + expiry_message

            messages.success(request, gettext(message))
        except Exception:
            messages.error(request, gettext("There was an error saving the submission."))
        return HttpResponseClientRedirect(reverse("recordtransfer:user_profile"))

    def save_form_data(self, request: HttpRequest) -> None:
        """Save the current state of the form to the database.

        Args:
            request: The HTTP request object.
        """
        ### Gather information to save ###

        current_data = SubmissionFormWizard.format_step_data(self.current_step, request.POST)
        form_data = {"past": self.storage.data, "current": current_data}

        title = None
        session_token = None
        # See if the title and session token are in the current data
        if isinstance(current_data, dict):
            title = current_data.get("accession_title")
            session_token = current_data.get("session_token")

        # Look in past data if not found in current data
        if not title:
            title = self.get_form_value(SubmissionStep.RECORD_DESCRIPTION, "accession_title")
        if not session_token:
            session_token = self.get_form_value(SubmissionStep.UPLOAD_FILES, "session_token")

        ### Save the information ###

        if self.in_progress_submission:
            self.in_progress_submission.last_updated = timezone.now()
        else:
            self.in_progress_submission = InProgressSubmission()

        self.in_progress_submission.title = title
        session = UploadSession.objects.filter(token=session_token, user=self.request.user).first()
        if session:
            self.in_progress_submission.upload_session = session

        self.in_progress_submission.current_step = self.current_step.value
        self.in_progress_submission.user = cast(User, self.request.user)
        self.in_progress_submission.step_data = pickle.dumps(form_data)

        self.in_progress_submission.save()

    def save_current_step(
        self, form: Union[BaseInlineFormSet, BaseModelFormSet, ModelForm]
    ) -> None:
        """Save the data from the current step."""
        self.storage.set_step_data(self.steps.current, self.process_step(form))
        self.storage.set_step_files(self.steps.current, self.process_step_files(form))

    def render_goto_step(self, goto_step: str, *args, **kwargs) -> HttpResponse:
        """Perform necessary validation and data saving before going to to desired step. Skips
        validation if the user is trying to go to a previous step. Otherwise, validates each form
        before the goto step, and takes user to the step with the first error if any form is
        invalid.
        """
        current_step_form = self.get_form(data=self.request.POST, files=self.request.FILES)
        self.save_current_step(current_step_form)

        # Get step indices
        goto_index = self.steps.all.index(goto_step)
        current_index = self.steps.all.index(self.steps.current)

        if goto_index > current_index:
            # Validate each form before the goto step
            for step in self.steps.all[:goto_index]:
                # Populate form with saved data
                form = (
                    current_step_form
                    if step == self.steps.current
                    else self.get_form(
                        step,
                        data=self.storage.get_step_data(step),
                        files=self.storage.get_step_files(step),
                    )
                )
                if not form.is_valid():
                    messages.error(self.request, gettext("Please correct the errors below."))
                    self.storage.current_step = step
                    return self.render(form, **kwargs)

        self.storage.current_step = goto_step
        next_form = self.get_form(
            data=self.storage.get_step_data(self.steps.current),
            files=self.storage.get_step_files(self.steps.current),
        )
        forms.clear_form_errors(next_form)
        return self.render(next_form, **kwargs)

    def render_next_step(self, form: Union[BaseForm, BaseFormSet], **kwargs) -> HttpResponse:
        """Render next step of form. Overrides parent method to clear errors from the form."""
        # Check if we just completed contact info step and user needs prompting
        user = cast(User, self.request.user)
        if (
            self.current_step == SubmissionStep.CONTACT_INFO
            and not user.has_contact_info
            and not self.storage.extra_data.get("save_contact_info_prompted", False)
        ):
            form = cast(forms.ContactInfoForm, form)
            self.storage.extra_data["save_contact_info_prompted"] = True
            return self.trigger_contact_info_save_prompt(form)

        # get the form instance based on the data from the storage backend
        # (if available).
        next_step = self.steps.next
        new_form = self.get_form(
            next_step,
            data=self.storage.get_step_data(next_step),
            files=self.storage.get_step_files(next_step),
        )
        ##########################
        # This part is different from the parent class. We need to clear the errors from the form
        forms.clear_form_errors(new_form)
        ##########################

        # change the stored current step
        self.storage.current_step = next_step
        return self.render(new_form, **kwargs)

    def trigger_contact_info_save_prompt(self, form: forms.ContactInfoForm) -> HttpResponse:
        """Trigger a prompt to save contact info using HTMX."""
        response = HttpResponse(status=200)
        data = form.cleaned_data
        return trigger_client_event(
            response,
            "promptSaveContactInfo",
            {
                "message": gettext(
                    "Would you like to save your contact information to your profile?"
                ),
                "contactInfo": {
                    "phone_number": data.get("phone_number", ""),
                    "address_line_1": data.get("address_line_1", ""),
                    "address_line_2": data.get("address_line_2", ""),
                    "city": data.get("city", ""),
                    "province_or_state": data.get("province_or_state", ""),
                    "other_province_or_state": data.get("other_province_or_state", ""),
                    "postal_or_zip_code": data.get("postal_or_zip_code", ""),
                    "country": data.get("country", ""),
                },
            },
        )

    @classmethod
    def format_step_data(cls, step: SubmissionStep, data: QueryDict) -> Union[dict, list[dict]]:
        """Format form data for the current step to be saved for later.

        Args:
            step: The current step of the form.
            data: The data from the form.

        Returns:
            The formatted step data. If this step represents a formset, the return object will be a
            list of dicts, otherwise, it will be a dict.
        """
        pattern = re.compile("^" + re.escape(step.value) + r"-(?:(?P<index>\d+)-)?(?P<field>.+)$")

        formatted_data = []
        is_formset = False

        for key, value in data.items():
            match_obj = pattern.match(key)

            if not match_obj:
                continue

            field: str = match_obj.group("field")
            index: str = match_obj.group("index")

            if field in {
                "MIN_NUM_FORMS",
                "MAX_NUM_FORMS",
                "TOTAL_FORMS",
                "INITIAL_FORMS",
            }:
                continue

            if index:
                index_num = int(index)
                is_formset = True
            else:
                index_num = 0

            while len(formatted_data) <= index_num:
                formatted_data.append({})

            formatted_data[index_num][field] = value

        if is_formset:
            # Remove any empty dictionaries if there were any created without data
            return [data for data in formatted_data if data]

        # Case where the form has no fields
        if len(formatted_data) == 0:
            return {}

        return formatted_data[0]

    def get_form_value(self, step: SubmissionStep, field: str) -> Optional[str]:
        """Get the value of a field in a form step.

        Args:
            step: The step of the form to get the field value from.
            field: The field to get the value of.

        Returns:
            The value of the field in the form step, or None if the is not populated.
        """
        step_data = self.storage.get_step_data(step.value) or {}
        return step_data.get(f"{step.value}-{field}")

    def get_template_names(self) -> list[str]:
        """Override the parent method to return the template name to render for the current
        step.
        """
        return [self._TEMPLATES[self.current_step].template]

    def get_name_of_user(self, user: User) -> str:
        """Get the name of a user.

        Tries to get the name from the User object first, and falls back to using the form data
        submitted in the contact info.
        """
        if user:
            if user.first_name and user.last_name:
                return f"{user.first_name} {user.last_name}"
            elif user.first_name:
                return user.first_name
            elif user.last_name:
                return user.last_name
        return self.get_form_value(SubmissionStep.CONTACT_INFO, "contact_name") or ""

    def get_form_initial(self, step: str) -> dict:
        """Populate the initial state of the form.

        Populate form with saved in-progress submission data if a "resume" request was received.
        Fills in the user's name and email automatically where possible.
        """
        initial = (self.initial_dict or {}).get(step, {})

        if self.in_progress_submission and step == self.in_progress_submission.current_step:
            initial = pickle.loads(self.in_progress_submission.step_data)["current"]

        if not self.in_progress_submission and step == SubmissionStep.CONTACT_INFO.value:
            user = cast(User, self.request.user)
            initial["contact_name"] = self.get_name_of_user(user)
            initial["email"] = str(user.email)
            initial["phone_number"] = user.phone_number or ""
            initial["address_line_1"] = user.address_line_1 or ""
            initial["address_line_2"] = user.address_line_2 or ""
            initial["city"] = user.city or ""
            initial["province_or_state"] = user.province_or_state or ""
            initial["other_province_or_state"] = user.other_province_or_state or ""
            initial["postal_or_zip_code"] = user.postal_or_zip_code or ""
            initial["country"] = user.country or ""

        return initial

    def get_form_kwargs(self, step: Optional[str] = None) -> dict:
        """Add data to inject when initializing the form."""
        kwargs = super().get_form_kwargs(step)

        if step == SubmissionStep.GROUP_SUBMISSION.value:
            kwargs["user"] = self.request.user

        elif step == SubmissionStep.SOURCE_INFO.value:
            source_type, _ = SourceType.objects.get_or_create(name="Individual")
            source_role, _ = SourceRole.objects.get_or_create(name="Donor")
            kwargs["defaults"] = {
                "source_name": self.get_name_of_user(self.request.user),  # type: ignore
                "source_type": source_type,
                "source_role": source_role,
            }

        return kwargs

    def get_forms_for_review(self) -> OrderedDict[str, Union[BaseForm, BaseFormSet]]:
        """Retrieve the relevant forms to be processed for the review step. This method does not
        validate the forms, but populates the cleaned_data attribute of each form.
        """
        final_forms = OrderedDict()
        form_list = self.get_form_list() or []
        for form_step in form_list:
            submission_step = SubmissionStep(form_step)
            if submission_step in (SubmissionStep.ACCEPT_LEGAL, SubmissionStep.REVIEW):
                continue
            form_obj = self.get_form(
                step=form_step,
                data=self.storage.get_step_data(form_step),
                files=self.storage.get_step_files(form_step),
            )
            form_obj.is_valid()  # This populates the cleaned_data attribute of the form
            final_forms[SubmissionFormWizard._TEMPLATES[SubmissionStep(form_step)].title] = (
                form_obj
            )
        return final_forms

    @property
    def review_step_reached(self) -> bool:
        """Check if the user has reached the review step at some point throughout this form. This
        check is valid for a resumed in-progress submission as well.
        """
        # If there are entries for every step of the form, then the review step has been reached
        return len(self.storage.data.get("step_data", [])) == self.steps.count

    @property
    def form_started(self) -> bool:
        """Check if the user has started the form. This is true if there is an in-progress
        submission, or if the user has submitted any data for the form.
        """
        return self.in_progress_submission is not None or bool(
            self.storage.data.get("step_data", {})
        )

    def get_context_data(self, form: Union[BaseForm, BaseFormSet], **kwargs) -> dict[str, Any]:
        """Retrieve context data for the current form template, including context for the
        JavaScript files used alongside the template.

        Args:
            form: The form to display to the user.
            **kwargs: Additional keyword arguments.

        Returns:
            dict: A dictionary of context data to be used to render the form template.
        """
        context = super().get_context_data(form, **kwargs)
        step_titles_dict = {step.value: meta.title for step, meta in self._TEMPLATES.items()}
        context["step_titles_dict"] = step_titles_dict

        context.update(
            {
                "form_title": self._TEMPLATES[self.current_step].title,
                "info_message": self._TEMPLATES[self.current_step].info_message,
            }
        )

        # Show the review button if the user has reached the step before the review step
        # or if they have reached the review step once before
        if self.steps.step1 < self.steps.count and (
            self.steps.step1 == self.steps.count - 1 or self.review_step_reached
        ):
            context["SHOW_REVIEW_BUTTON"] = True

        # Show the save button if the user has started the form and is not on the Review Step
        if self.form_started and self.steps.step1 != self.steps.count:
            context["SHOW_SAVE_BUTTON"] = True

        # Add template and JS contexts
        context.update(self._get_template_context())
        context["js_context"] = self._get_javascript_context()
        context["js_context_id"] = "js_context_" + self.steps.current

        return context

    def _get_template_context(self) -> dict[str, Any]:
        """Retrieve context data for the current form template.

        Returns:
            A dictionary of context data to be used to render the form template.
        """
        context = {}

        if self.current_step == SubmissionStep.GROUP_SUBMISSION:
            context.update(
                {
                    "new_group_form": forms.SubmissionGroupForm(),
                }
            )

        elif self.current_step == SubmissionStep.UPLOAD_FILES:
            context.update(
                {
                    "MAX_TOTAL_UPLOAD_SIZE_MB": settings.MAX_TOTAL_UPLOAD_SIZE_MB,
                    "MAX_SINGLE_UPLOAD_SIZE_MB": settings.MAX_SINGLE_UPLOAD_SIZE_MB,
                    "MAX_TOTAL_UPLOAD_COUNT": settings.MAX_TOTAL_UPLOAD_COUNT,
                    "ACCEPTED_FILE_FORMATS": settings.ACCEPTED_FILE_FORMATS,
                }
            )

        elif self.current_step == SubmissionStep.REVIEW:
            context["form_list"] = forms.ReviewForm.format_form_data(
                self.get_forms_for_review(), user=cast(User, self.request.user)
            )
        return context

    def _get_javascript_context(self) -> dict[str, Any]:
        """Get context for the current form template that gets passed to the JavaScript files.

        Returns:
            A dictionary of context data to be used in the JavaScript files. Can be empty.
        """
        js_context: dict[str, Any] = {"FORM_STARTED": self.form_started}

        step = self.current_step
        if step == SubmissionStep.CONTACT_INFO:
            js_context.update(
                {
                    "id_province_or_state": HtmlIds.ID_CONTACT_INFO_PROVINCE_OR_STATE,
                    "id_other_province_or_state": HtmlIds.ID_CONTACT_INFO_OTHER_PROVINCE_OR_STATE,
                    "other_province_or_state_value": OtherValues.PROVINCE_OR_STATE,
                    "account_info_update_url": reverse("recordtransfer:contact_info_update"),
                }
            )

        elif step == SubmissionStep.RIGHTS:
            other_rights = RightsType.objects.filter(name="Other").first()

            js_context.update(
                {
                    "formset_prefix": SubmissionStep.RIGHTS.value,
                    "other_rights_type_id": other_rights.pk if other_rights else 0,
                }
            )
        elif step == SubmissionStep.OTHER_IDENTIFIERS:
            js_context.update(
                {
                    "formset_prefix": SubmissionStep.OTHER_IDENTIFIERS.value,
                },
            )
        elif step == SubmissionStep.SOURCE_INFO:
            other_role = SourceRole.objects.filter(name="Other").first()
            other_type = SourceType.objects.filter(name="Other").first()

            js_context.update(
                {
                    "id_enter_manual_source_info": HtmlIds.ID_SOURCE_INFO_ENTER_MANUAL_SOURCE_INFO,
                    "id_source_type": HtmlIds.ID_SOURCE_INFO_SOURCE_TYPE,
                    "id_other_source_type": HtmlIds.ID_SOURCE_INFO_OTHER_SOURCE_TYPE,
                    "id_source_role": HtmlIds.ID_SOURCE_INFO_SOURCE_ROLE,
                    "id_other_source_role": HtmlIds.ID_SOURCE_INFO_OTHER_SOURCE_ROLE,
                    "other_role_id": other_role.pk if other_role else 0,
                    "other_type_id": other_type.pk if other_type else 0,
                }
            )
        elif step == SubmissionStep.GROUP_SUBMISSION:
            js_context.update(
                {
                    "ID_SUBMISSION_GROUP_NAME": HtmlIds.ID_SUBMISSION_GROUP_NAME,
                    "id_submission_group_description": HtmlIds.ID_SUBMISSION_GROUP_DESCRIPTION,
                    "id_display_group_description": HtmlIds.ID_DISPLAY_GROUP_DESCRIPTION,
                    "id_submission_group_selection": HtmlIds.ID_SUBMISSION_GROUP_SELECTION,
                    "fetch_group_descriptions_url": reverse(
                        "recordtransfer:get_user_submission_groups",
                    ),
                    "default_group_uuid": self.submission_group_uuid,
                    "FRONTEND_REQUEST_HEADER": HeaderNames.FRONTEND_REQUEST,
                },
            )
        elif step == SubmissionStep.UPLOAD_FILES:
            js_context.update(
                {
                    "MAX_TOTAL_UPLOAD_SIZE_MB": settings.MAX_TOTAL_UPLOAD_SIZE_MB,
                    "MAX_SINGLE_UPLOAD_SIZE_MB": settings.MAX_SINGLE_UPLOAD_SIZE_MB,
                    "MAX_TOTAL_UPLOAD_COUNT": settings.MAX_TOTAL_UPLOAD_COUNT,
                    "ACCEPTED_FILE_FORMATS": [
                        f".{format}"
                        for formats in settings.ACCEPTED_FILE_FORMATS.values()
                        for format in formats
                    ],
                }
            )
        return js_context

    def done(self, form_list: list[BaseForm], **kwargs) -> HttpResponse:
        """Retrieve all of the form data, and creates a Submission from it.

        Args:
            form_list: A list of all the forms in the form wizard.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: A redirect to the submission sent page, or an error page if there was an
            unexpected issue creating the submission.
        """
        form_data = {}
        try:
            form_data = self.get_all_cleaned_data()

            submission = Submission.objects.create(
                user=self.request.user, raw_form=pickle.dumps(form_data)
            )

            LOGGER.info("Mapping form data to CAAIS metadata")
            submission.metadata = map_form_to_metadata(form_data)

            if settings.FILE_UPLOAD_ENABLED and (
                upload_session := UploadSession.objects.filter(
                    token=form_data["session_token"]
                ).first()
            ):
                submission.upload_session = upload_session
                submission.upload_session.make_uploads_permanent()  # type: ignore
            else:
                LOGGER.info(
                    (
                        "No file upload session will be linked to submission due to "
                        "FILE_UPLOAD_ENABLED=false"
                    )
                )

            submission.part_of_group = form_data.get("submission_group")

            LOGGER.info("Saving Submission with UUID %s", str(submission.uuid))
            submission.save()

            if self.in_progress_submission:
                self.in_progress_submission.delete()

            send_submission_creation_success.delay(form_data, submission)
            send_thank_you_for_your_submission.delay(form_data, submission)

            return HttpResponseRedirect(reverse("recordtransfer:submission_sent"))

        except Exception as exc:
            LOGGER.error("Encountered error creating Submission object", exc_info=exc)

            send_your_submission_did_not_go_through.delay(form_data, cast(User, self.request.user))
            send_submission_creation_failure.delay(form_data, cast(User, self.request.user))

            raise Exception(
                gettext(
                    "There was an error creating your submission. Please try again later or contact "
                    "us for assistance."
                )
            ) from exc
