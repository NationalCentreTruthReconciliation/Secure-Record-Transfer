import logging
import pickle
from typing import Any, ClassVar, Optional, Union

from caais.export import ExportVersion
from caais.models import RightsType, SourceRole, SourceType
from clamav.scan import check_for_malware
from django.conf import settings as djangosettings
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db.models.base import Model as Model
from django.forms import BaseModelForm
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
    QueryDict,
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.text import slugify
from django.utils.translation import gettext
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, FormView, TemplateView, UpdateView, View
from formtools.wizard.views import SessionWizardView

from recordtransfer import settings
from recordtransfer.caais import map_form_to_metadata
from recordtransfer.constants import (
    ID_CONFIRM_NEW_PASSWORD,
    ID_CURRENT_PASSWORD,
    ID_DISPLAY_GROUP_DESCRIPTION,
    ID_GETS_NOTIFICATION_EMAILS,
    ID_NEW_PASSWORD,
    ID_SUBMISSION_GROUP_DESCRIPTION,
    ID_SUBMISSION_GROUP_NAME,
    ID_SUBMISSION_GROUP_SELECTION,
)
from recordtransfer.emails import (
    send_submission_creation_failure,
    send_submission_creation_success,
    send_thank_you_for_your_transfer,
    send_user_account_updated,
    send_user_activation_email,
    send_your_transfer_did_not_go_through,
)
from recordtransfer.enums import TransferStep
from recordtransfer.forms import SignUpForm, UserProfileForm
from recordtransfer.forms.submission_group_form import SubmissionGroupForm
from recordtransfer.models import (
    InProgressSubmission,
    Submission,
    SubmissionGroup,
    UploadedFile,
    UploadSession,
    User,
)
from recordtransfer.tokens import account_activation_token
from recordtransfer.utils import get_human_readable_file_count, get_human_readable_size

LOGGER = logging.getLogger(__name__)


class Index(TemplateView):
    """The homepage."""

    template_name = "recordtransfer/home.html"


def media_request(request: HttpRequest, path: str) -> HttpResponse:
    """Respond to whether a media request is allowed or not."""
    if not request.user.is_authenticated:
        return HttpResponseForbidden("You do not have permission to access this resource.")

    if not path:
        return HttpResponseNotFound("The requested resource could not be found")

    user = request.user
    if not user.is_staff:
        return HttpResponseForbidden("You do not have permission to access this resource.")

    response = HttpResponse(
        headers={"X-Accel-Redirect": djangosettings.MEDIA_URL + path.lstrip("/")}
    )

    # Nginx will assign its own headers for the following:
    del response["Content-Type"]
    del response["Content-Disposition"]
    del response["Accept-Ranges"]
    del response["Set-Cookie"]
    del response["Cache-Control"]
    del response["Expires"]

    return response


class TransferSent(TemplateView):
    """The page a user sees when they finish a transfer."""

    template_name = "recordtransfer/transfersent.html"


class SystemErrorPage(TemplateView):
    """The page a user sees when there is some system error."""

    template_name = "recordtransfer/systemerror.html"


class UserProfile(UpdateView):
    """View to show two things:
    - The user's profile information
    - A list of the Submissions a user has created via transfer.
    """

    template_name = "recordtransfer/profile.html"
    paginate_by = 10
    form_class = UserProfileForm
    success_url = reverse_lazy("recordtransfer:userprofile")
    success_message = gettext("Preferences updated")
    password_change_success_message = gettext("Password updated")
    error_message = gettext("There was an error updating your preferences. Please try again.")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add context data for the user profile view."""
        context = super().get_context_data(**kwargs)
        context["in_progress_submissions"] = InProgressSubmission.objects.filter(
            user=self.request.user
        ).order_by("-last_updated")
        context["user_submissions"] = Submission.objects.filter(user=self.request.user).order_by(
            "-submission_date"
        )
        context["submission_groups"] = SubmissionGroup.objects.filter(
            created_by=self.request.user
        ).order_by("name")

        context["ID_GETS_NOTIFICATION_EMAILS"] = ID_GETS_NOTIFICATION_EMAILS
        context["ID_CURRENT_PASSWORD"] = ID_CURRENT_PASSWORD
        context["ID_NEW_PASSWORD"] = ID_NEW_PASSWORD
        context["ID_CONFIRM_NEW_PASSWORD"] = ID_CONFIRM_NEW_PASSWORD
        return context

    def get_form_kwargs(self) -> dict[str, Any]:
        """Pass User instance to form to initialize it."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.get_object()
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
        return super().form_invalid(form)


class About(TemplateView):
    """About the application."""

    template_name = "recordtransfer/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["accepted_files"] = settings.ACCEPTED_FILE_FORMATS
        context["max_total_upload_size"] = settings.MAX_TOTAL_UPLOAD_SIZE
        context["max_single_upload_size"] = settings.MAX_SINGLE_UPLOAD_SIZE
        context["max_total_upload_count"] = settings.MAX_TOTAL_UPLOAD_COUNT
        return context


class ActivationSent(TemplateView):
    """The page a user sees after creating an account."""

    template_name = "recordtransfer/activationsent.html"


class ActivationComplete(TemplateView):
    """The page a user sees when their account has been activated."""

    template_name = "recordtransfer/activationcomplete.html"


class ActivationInvalid(TemplateView):
    """The page a user sees if their account could not be activated."""

    template_name = "recordtransfer/activationinvalid.html"


class CreateAccount(FormView):
    """Allows a user to create a new account with the SignUpForm. When the form is submitted
    successfully, send an email to that user with a link that lets them activate their account.
    """

    template_name = "recordtransfer/signupform.html"
    form_class = SignUpForm
    success_url = reverse_lazy("recordtransfer:activationsent")

    def form_valid(self, form):
        new_user = form.save(commit=False)
        new_user.is_active = False
        new_user.gets_submission_email_updates = False
        new_user.save()
        send_user_activation_email.delay(new_user)
        return super().form_valid(form)


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.confirmed_email = True
        user.save()
        login(request, user)
        return HttpResponseRedirect(reverse("recordtransfer:accountcreated"))

    return HttpResponseRedirect(reverse("recordtransfer:activationinvalid"))


class TransferFormWizard(SessionWizardView):
    """A multi-page form for collecting user metadata and uploading files. Uses a form wizard. For
    more info, visit this link: https://django-formtools.readthedocs.io/en/latest/wizard.html.
    """

    _TEMPLATES: ClassVar[dict[TransferStep, dict[str, str]]] = {
        TransferStep.ACCEPT_LEGAL: {
            "templateref": "recordtransfer/transferform_legal.html",
            "formtitle": gettext("Legal Agreement"),
        },
        TransferStep.CONTACT_INFO: {
            "templateref": "recordtransfer/transferform_standard.html",
            "formtitle": gettext("Contact Information"),
            "infomessage": gettext(
                "Enter your contact information in case you need to be contacted by one of our "
                "archivists regarding your transfer"
            ),
        },
        TransferStep.SOURCE_INFO: {
            "templateref": "recordtransfer/transferform_sourceinfo.html",
            "formtitle": gettext("Source Information"),
            "infomessage": gettext(
                "Enter the info for the source of the records. The source is the person or entity "
                "that created the records or is holding the records at the moment. If this is you, "
                "put your own information in"
            ),
        },
        TransferStep.RECORD_DESCRIPTION: {
            "templateref": "recordtransfer/transferform_standard.html",
            "formtitle": gettext("Record Description"),
            "infomessage": gettext(
                "Provide a brief description of the records you're transferring"
            ),
        },
        TransferStep.RIGHTS: {
            "templateref": "recordtransfer/transferform_rights.html",
            "formtitle": gettext("Record Rights"),
            "infomessage": gettext(
                "Enter any associated rights that apply to the records. Add as many rights "
                "sections as you like using the + More button. You may enter another type of "
                "rights if the dropdown does not contain the type of rights you're looking for."
            ),
        },
        TransferStep.OTHER_IDENTIFIERS: {
            "templateref": "recordtransfer/transferform_formset.html",
            "formtitle": gettext("Other Identifiers (Optional)"),
            "infomessage": gettext(
                "This step is optional, if you do not have any other IDs associated with the "
                "records, go to the next step"
            ),
        },
        TransferStep.GROUP_TRANSFER: {
            "templateref": "recordtransfer/transferform_group.html",
            "formtitle": gettext("Assign Transfer to Group (Optional)"),
            "infomessage": gettext(
                "If this transfer belongs in a group with other transfers you have made or will "
                "make, select the group it belongs in in the dropdown below, or create a new group"
            ),
        },
        TransferStep.UPLOAD_FILES: {
            "templateref": "recordtransfer/transferform_dropzone.html",
            "formtitle": gettext("Upload Files"),
            "infomessage": gettext(
                "Add any final notes you would like to add, and upload your files"
            ),
        },
        TransferStep.FINAL_NOTES: {
            "templateref": "recordtransfer/transferform_standard.html",
            "formtitle": gettext("Final Notes"),
            "infomessage": gettext("Add any final notes that may not have fit in previous steps"),
        },
    }

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Dispatch the request to the appropriate handler method."""
        result = self.validate_transfer_request(request)
        if isinstance(result, HttpResponse):
            return result
        return super().dispatch(request, *args, **kwargs)

    def validate_transfer_request(self, request) -> Optional[HttpResponse]:
        """Validate the transfer request and return an appropriate response if invalid."""
        self.submission_group_uuid = None
        self.in_progress_submission = None
        self.in_progress_uuid = request.GET.get("transfer_uuid")

        # Handle no transfer UUID case
        if not self.in_progress_uuid:
            self.submission_group_uuid = request.GET.get("group_uuid")
            return None

        # Handle transfer UUID case
        try:
            self.in_progress_submission = InProgressSubmission.objects.filter(
                user=request.user, uuid=self.in_progress_uuid
            ).first()
        except ValidationError:
            LOGGER.error("Invalid UUID %s", self.in_progress_uuid)
            return redirect("recordtransfer:transfer")

        if not self.in_progress_submission:
            LOGGER.error(
                "Expected at least 1 saved transfer for user %s and ID %s, found 0",
                request.user,
                self.in_progress_uuid,
            )
            return redirect("recordtransfer:transfer")

        return None

    def get(self, request, *args, **kwargs):
        if self.in_progress_submission:
            self.load_transfer_data(self.in_progress_submission)
            return self.render(self.get_form())

        return super().get(self, request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle POST request to save a transfer."""
        save_form_step = request.POST.get("save_form_step", None)

        if not save_form_step:
            return super().post(request, *args, **kwargs)

        past_data = self.storage.data
        current_data = TransferFormWizard.format_step_data(save_form_step, request.POST)

        title = current_data.get("accession_title")
        if not title:
            title = self.get_form_value("recorddescription", "accession_title")

        data = {
            "save_form_step": save_form_step,
            "form_data": {"past": past_data, "current": current_data},
            "submission": self.in_progress_submission,
            "title": title,
        }

        try:
            self.save_transfer(data)
            messages.success(request, gettext("Transfer saved successfully."))
        except Exception:
            messages.error(request, gettext("There was an error saving the transfer."))
        return redirect("recordtransfer:userprofile")

    def load_transfer_data(self, transfer: InProgressSubmission) -> None:
        """Load the transfer data from an InProgressSubmission instance."""
        self.storage.data = pickle.loads(transfer.step_data)["past"]
        self.storage.current_step = transfer.current_step

    @classmethod
    def format_step_data(cls, step: str, data: QueryDict) -> dict:
        """Format the step data by stripping the step prefix from the keys.

        Args:
            step (str): The current step of the form.
            data (QueryDict): The data from the form.

        Returns:
            dict: The formatted step data.
        """
        return {f.replace(step + "-", ""): data[f] for f in data if f.startswith(step + "-")}

    def save_transfer(self, data: dict) -> None:
        """Save the current state of a transfer.

        Args:
            user: The user who is saving the transfer.
            data: The form data containing the submission data to save.
            `data` is a dictionary containing the following:
                - save_form_step: The current step of the form.
                - step_data: The past and current data of the form.
                - submission (optional): The in-progress submission model object to update.
                - title: The accession title of the submission.

        Returns:
            A JSON response indicating the result of the save operation.
        """
        submission = data.get("submission")
        form_data = data.get("form_data")
        save_form_step = data.get("save_form_step")
        title = data.get("title")

        if not form_data or not save_form_step:
            raise ValueError("Missing form data or save form step")

        if submission:
            submission.last_updated = timezone.now()
        else:
            submission = InProgressSubmission()

        submission.current_step = save_form_step
        submission.user = self.request.user
        submission.step_data = pickle.dumps(form_data)
        submission.title = title
        submission.save()

    def get_form_value(self, step: str, field: str) -> Optional[str]:
        """Get the value of a field in a form step.

        Args:
            step: The step of the form to get the field value from.
            field: The field to get the value of.

        Returns:
            The value of the field in the form step, or None if the is not populated.
        """
        step_data = self.storage.get_step_data(step) or {}
        return step_data.get(f"{step}-{field}")

    def get_template_names(self):
        """Retrieve the name of the template for the current step."""
        step_name = self.steps.current
        return [self._TEMPLATES[step_name]["templateref"]]

    def get_form_initial(self, step):
        """Populate form with saved transfer data (if a "resume" request was received), and add the
        user's name and email from their user profile.
        """
        initial = self.initial_dict.get(step, {})

        if self.in_progress_submission and step == self.in_progress_submission.current_step:
                data = pickle.loads(self.in_progress_submission.step_data)["current"]
                for k, v in data.items():
                    initial[k] = v

        if step == "contactinfo":
            curr_user = self.request.user
            if curr_user.first_name and curr_user.last_name:
                initial["contact_name"] = f"{curr_user.first_name} {curr_user.last_name}"
            initial["email"] = str(curr_user.email)

        return initial

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == "grouptransfer":
            kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, form, **kwargs):
        """Retrieve context data for the current form template.

        Args:
            form: The form to display to the user.

        Returns:
            dict: A dictionary of context data to be used to render the form template.
        """
        context = super().get_context_data(form, **kwargs)
        step_name = self.steps.current

        context.update({"form_title": self._TEMPLATES[step_name]["formtitle"]})

        if "infomessage" in self._TEMPLATES[step_name]:
            context.update({"info_message": self._TEMPLATES[step_name]["infomessage"]})

        if step_name == "grouptransfer":
            context.update(
                {
                    "IS_NEW": True,
                    "new_group_form": SubmissionGroupForm(),
                    "ID_SUBMISSION_GROUP_NAME": ID_SUBMISSION_GROUP_NAME,
                    "ID_SUBMISSION_GROUP_DESCRIPTION": ID_SUBMISSION_GROUP_DESCRIPTION,
                    "ID_DISPLAY_GROUP_DESCRIPTION": ID_DISPLAY_GROUP_DESCRIPTION,
                    "ID_SUBMISSION_GROUP_SELECTION": ID_SUBMISSION_GROUP_SELECTION,
                    "DEFAULT_GROUP_ID": self.submission_group_uuid,
                    "MODAL_MODE": True,
                }
            )

        elif step_name == "rights":
            all_rights = RightsType.objects.all().exclude(name="Other")
            context.update({"rights": all_rights})

        elif step_name == "sourceinfo":
            all_roles = SourceRole.objects.all().exclude(name="Other")
            all_types = SourceType.objects.all().exclude(name="Other")
            context.update(
                {
                    "source_roles": all_roles,
                    "source_types": all_types,
                }
            )

        return context

    def get_all_cleaned_data(self):
        """Clean data, and populate CAAIS fields that are deferred to being created until after the
        submission is completed.
        """
        cleaned_data = super().get_all_cleaned_data()
        self.set_quantity_and_unit_of_measure(cleaned_data)
        return cleaned_data

    def set_quantity_and_unit_of_measure(self, cleaned_data):
        """Create a summary for the quantity_and_unit_of_measure from the type of files submitted.

        Args:
            cleaned_data (dict): The cleaned data submitted by the user

        Returns:
            (None): The cleaned form data is modified in-place
        """
        if not settings.FILE_UPLOAD_ENABLED:
            return

        session = UploadSession.objects.filter(token=cleaned_data["session_token"]).first()

        size = get_human_readable_size(session.upload_size, base=1024, precision=2)

        count = get_human_readable_file_count(
            [f.name for f in session.get_existing_file_set()],
            settings.ACCEPTED_FILE_FORMATS,
            LOGGER,
        )

        cleaned_data["quantity_and_unit_of_measure"] = gettext("{0}, totalling {1}").format(
            count, size
        )

    def done(self, form_list, **kwargs):
        """Retrieve all of the form data, and creates a Submission from it.

        Returns:
            HttpResponseRedirect: Redirects the user to their User Profile page.
        """
        try:
            form_data = self.get_all_cleaned_data()

            submission = Submission.objects.create(
                user=self.request.user, raw_form=pickle.dumps(form_data)
            )

            LOGGER.info("Mapping form data to CAAIS metadata")
            submission.metadata = map_form_to_metadata(form_data)

            if settings.FILE_UPLOAD_ENABLED:
                token = form_data["session_token"]
                LOGGER.info("Fetching session with the token %s", token)
                submission.upload_session = UploadSession.objects.filter(token=token).first()
            else:
                LOGGER.info(
                    (
                        "No file upload session will be linked to submission due to "
                        "FILE_UPLOAD_ENABLED=false"
                    )
                )

            submission.part_of_group = self.get_submission_group(form_data)

            LOGGER.info("Saving Submission with UUID %s", str(submission.uuid))
            submission.save()

            send_submission_creation_success.delay(form_data, submission)
            send_thank_you_for_your_transfer.delay(form_data, submission)

            return HttpResponseRedirect(reverse("recordtransfer:userprofile"))

        except Exception as exc:
            LOGGER.error("Encountered error creating Submission object", exc_info=exc)

            send_your_transfer_did_not_go_through.delay(form_data, self.request.user)
            send_submission_creation_failure.delay(form_data, self.request.user)

            return HttpResponseRedirect(reverse("recordtransfer:systemerror"))

    def get_submission_group(self, cleaned_form_data: dict) -> Optional[SubmissionGroup]:
        """Get a submission group to associate the submission with, depending on how the user
        filled out the submission group section of the form.
        """
        group = None

        group_id = cleaned_form_data["group_id"]
        if group_id:
            try:
                group = SubmissionGroup.objects.get(uuid=group_id, created_by=self.request.user)
                LOGGER.info('Associating Submission with "%s" SubmissionGroup', group.name)

            except SubmissionGroup.DoesNotExist as exc:
                LOGGER.error("Could not find SubmissionGroup with UUID %s", group_id, exc_info=exc)
        else:
            LOGGER.info("Not associating submission with a group")

        return group


def get_in_progress_submission(user: User, uuid: str) -> Optional[InProgressSubmission]:
    """Retrieve an in-progress submission for a given user and UUID."""
    return InProgressSubmission.objects.filter(user=user, uuid=uuid).first()


@require_http_methods(["POST"])
def uploadfiles(request):
    """Upload one or more files to the server, and return a token representing the file upload
    session. If a token is passed in the request header using the Upload-Session-Token header, the
    uploaded files will be added to the corresponding session, meaning this endpoint can be hit
    multiple times for a large batch upload of files.

    Each file type is checked against this application's ACCEPTED_FILE_FORMATS setting, if any
    file is not an accepted type, an error message is returned.

    Args:
        request: The POST request sent by the user.

    Returns:
        JsonResponse: If the upload was successful, the session token is returned in
            'upload_session_token'. If not successful, the error description is returned in 'error',
            and a more verbose error is returned in 'verboseError'.
    """
    if not request.FILES:
        return JsonResponse(
            {
                "error": gettext("No files were uploaded"),
                "verboseError": gettext("No files were uploaded"),
            },
            status=400,
        )

    try:
        headers = request.headers
        if not "Upload-Session-Token" in headers or not headers["Upload-Session-Token"]:
            session = UploadSession.new_session()
            session.save()
        else:
            session = UploadSession.objects.filter(token=headers["Upload-Session-Token"]).first()
            if session is None:
                session = UploadSession.new_session()
                session.save()

        issues = []
        for _file in request.FILES.dict().values():
            file_check = _accept_file(_file.name, _file.size)
            if not file_check["accepted"]:
                _file.close()
                issues.append({"file": _file.name, **file_check})
                continue

            session_check = _accept_session(_file.name, _file.size, session)
            if not session_check["accepted"]:
                _file.close()
                issues.append({"file": _file.name, **session_check})
                continue

            try:
                check_for_malware(_file)

            except ValidationError as exc:
                LOGGER.error("Malware was found in the file %s", _file.name, exc_info=exc)
                _file.close()
                issues.append(
                    {
                        "file": _file.name,
                        "accepted": False,
                        "error": gettext("Malware detected in file"),
                        "verboseError": gettext(
                            f'Malware was detected in the file "{_file.name}"'
                        ),
                    }
                )
                continue

            new_file = UploadedFile(session=session, file_upload=_file, name=_file.name)
            new_file.save()

        return JsonResponse({"uploadSessionToken": session.token, "issues": issues}, status=200)

    except Exception as exc:
        LOGGER.error(msg=("Uncaught exception in uploadfiles view: {0}".format(str(exc))))
        return JsonResponse(
            {
                "error": gettext("500 Internal Server Error"),
                "verboseError": gettext("500 Internal Server Error"),
            },
            status=500,
        )


@require_http_methods(["GET", "POST"])
def accept_file(request):
    """Check whether the file is allowed to be uploaded by inspecting the file's extension. The
    allowed file extensions are set using the ACCEPTED_FILE_FORMATS setting.

    Args:
        request: The request sent by the user. This request should either be a GET or a POST
            request, with the name of the file in the **filename** parameter.

    Returns:
        JsonResponse: If the file is allowed to be uploaded, 'accepted' will be True. Otherwise,
            'accepted' is False and both 'error' and 'verboseError' are set.
    """
    # Ensure required parameters are set
    request_params = request.POST if request.method == "POST" else request.GET
    for required in ("filename", "filesize"):
        if required not in request_params:
            return JsonResponse(
                {
                    "accepted": False,
                    "error": gettext("Could not find {0} parameter in request").format(required),
                },
                status=400,
            )
        if not request_params[required]:
            return JsonResponse(
                {
                    "accepted": False,
                    "error": gettext("{0} parameter cannot be empty").format(required),
                },
                status=400,
            )

    filename = request_params["filename"]
    filesize = request_params["filesize"]
    token = request.headers.get("Upload-Session-Token", None)

    try:
        file_check = _accept_file(filename, filesize)
        if not file_check["accepted"]:
            return JsonResponse(file_check, status=200)

        if token:
            session = UploadSession.objects.filter(token=token).first()
            if session:
                session_check = _accept_session(filename, filesize, session)
                if not session_check["accepted"]:
                    return JsonResponse(session_check, status=200)

        # The contents of the file are not known here, so it is not necessary to
        # call _accept_content()

        return JsonResponse({"accepted": True}, status=200)

    except Exception as exc:
        LOGGER.error(msg=("Uncaught exception in checkfile view: {0}".format(str(exc))))
        return JsonResponse(
            {
                "accepted": False,
                "error": gettext("500 Internal Server Error"),
                "verboseError": gettext("500 Internal Server Error"),
            },
            status=500,
        )


def _accept_file(filename: str, filesize: Union[str, int]) -> dict:
    """Determine if a new file should be accepted. Does not check the file's
    contents, only its name and its size.

    These checks are applied:
    - The file name is not empty
    - The file has an extension
    - The file's extension exists in ACCEPTED_FILE_FORMATS
    - The file's size is an integer greater than zero
    - The file's size is less than or equal to the maximum allowed size for one file

    Args:
        filename (str): The name of the file
        filesize (Union[str, int]): A string or integer representing the size of
            the file (in bytes)

    Returns:
        (dict): A dictionary containing an 'accepted' key that contains True if
            the session is valid, or False if not. The dictionary also contains
            an 'error' and 'verboseError' key if 'accepted' is False.
    """
    def mib_to_bytes(m):
        return m * 1024 ** 2
    def bytes_to_mib(b):
        return b / 1024 ** 2

    # Check extension exists
    name_split = filename.split(".")
    if len(name_split) == 1:
        return {
            "accepted": False,
            "error": gettext("File is missing an extension."),
            "verboseError": gettext('The file "{0}" does not have a file extension').format(
                filename
            ),
        }

    # Check extension is allowed
    extension = name_split[-1].lower()
    extension_accepted = False
    for _, accepted_extensions in settings.ACCEPTED_FILE_FORMATS.items():
        for accepted_extension in accepted_extensions:
            if extension == accepted_extension.lower():
                extension_accepted = True
                break

    if not extension_accepted:
        return {
            "accepted": False,
            "error": gettext('Files with "{0}" extension are not allowed.').format(extension),
            "verboseError": gettext('The file "{0}" has an invalid extension (.{1})').format(
                filename, extension
            ),
        }

    # Check filesize is an integer
    size = filesize
    try:
        size = int(filesize)
        if size < 0:
            raise ValueError("File size cannot be negative")
    except ValueError:
        return {
            "accepted": False,
            "error": gettext("File size is invalid."),
            "verboseError": gettext('The file "{0}" has an invalid size ({1})').format(
                filename, size
            ),
        }

    # Check file has some contents (i.e., non-zero size)
    if size == 0:
        return {
            "accepted": False,
            "error": gettext("File is empty."),
            "verboseError": gettext('The file "{0}" is empty').format(filename),
        }

    # Check file size is less than the maximum allowed size for a single file
    max_single_size = min(settings.MAX_SINGLE_UPLOAD_SIZE, settings.MAX_TOTAL_UPLOAD_SIZE)
    max_single_size_bytes = mib_to_bytes(max_single_size)
    size_mib = bytes_to_mib(size)
    if size > max_single_size_bytes:
        return {
            "accepted": False,
            "error": gettext("File is too big ({0:.2f}MiB). Max filesize: {1}MiB").format(
                size_mib, max_single_size
            ),
            "verboseError": gettext(
                'The file "{0}" is too big ({1:.2f}MiB). Max filesize: {2}MiB'
            ).format(filename, size_mib, max_single_size),
        }

    # All checks succeded
    return {"accepted": True}


def _accept_session(filename: str, filesize: Union[str, int], session: UploadSession) -> dict:
    """Determine if a new file should be accepted as part of the session.

    These checks are applied:
    - The session has room for more files according to the MAX_TOTAL_UPLOAD_COUNT
    - The session has room for more files according to the MAX_TOTAL_UPLOAD_SIZE
    - A file with the same name has not already been uploaded

    Args:
        filename (str): The name of the file
        filesize (Union[str, int]): A string or integer representing the size of
            the file (in bytes)
        session (UploadSession): The session files are being uploaded to

    Returns:
        (dict): A dictionary containing an 'accepted' key that contains True if
            the session is valid, or False if not. The dictionary also contains
            an 'error' and 'verboseError' key if 'accepted' is False.
    """
    if not session:
        return {"accepted": True}

    def mib_to_bytes(m):
        return m * 1024 ** 2

    # Check number of files is within allowed total
    if session.number_of_files_uploaded() >= settings.MAX_TOTAL_UPLOAD_COUNT:
        return {
            "accepted": False,
            "error": gettext("You can not upload anymore files."),
            "verboseError": gettext(
                'The file "{0}" would push the total file count past the '
                "maximum number of files ({1})"
            ).format(filename, settings.MAX_TOTAL_UPLOAD_SIZE),
        }

    # Check total size of all files plus current one is within allowed size
    max_size = max(settings.MAX_SINGLE_UPLOAD_SIZE, settings.MAX_TOTAL_UPLOAD_SIZE)
    max_remaining_size_bytes = mib_to_bytes(max_size) - session.upload_size
    if int(filesize) > max_remaining_size_bytes:
        return {
            "accepted": False,
            "error": gettext("Maximum total upload size ({0} MiB) exceeded").format(max_size),
            "verboseError": gettext(
                'The file "{0}" would push the total transfer size past the ' "{1}MiB max"
            ).format(filename, max_size),
        }

    # Check that a file with this name has not already been uploaded
    filename_list = session.uploadedfile_set.all().values_list("name", flat=True)
    if filename in filename_list:
        return {
            "accepted": False,
            "error": gettext("A file with the same name has already been uploaded."),
            "verboseError": gettext('A file with the name "{0}" has already been uploaded').format(
                filename
            ),
        }

    # All checks succeded
    return {"accepted": True}


class DeleteTransfer(TemplateView):
    """View to handle the deletion of an in-progress submission."""

    template_name = "recordtransfer/transfer_delete.html"
    success_message = gettext("In-progress submission deleted")
    error_message = gettext("There was an error deleting the in-progress submission")
    model = InProgressSubmission
    context_object_name = "transfer"

    def get_object(self, queryset=None) -> InProgressSubmission:
        """Retrieve the InProgressSubmission object based on the UUID in the URL."""
        return get_object_or_404(InProgressSubmission, uuid=self.kwargs.get("uuid"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = self.get_object()
        return context

    def post(self, request, *args, **kwargs):
        try:
            uuid = self.kwargs["uuid"]
            submission = InProgressSubmission.objects.filter(
                user=self.request.user, uuid=uuid
            ).first()
            if submission:
                submission.delete()
                messages.success(request, self.success_message)
            else:
                LOGGER.error("Could not find in-progress submission with UUID %s", uuid)
                messages.error(request, self.error_message)
        except KeyError:
            LOGGER.error("No UUID provided for deletion")
        return redirect("recordtransfer:userprofile")


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
        return HttpResponseForbidden("You do not have permission to access this page.")

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

    def handle_no_permission(self) -> HttpResponseForbidden:
        return HttpResponseForbidden("You do not have permission to access this page.")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Pass submissions associated with the group to the template."""
        context = super().get_context_data(**kwargs)
        context["submissions"] = Submission.objects.filter(part_of_group=self.get_object())
        context["IS_NEW"] = False
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
        if "transfer" in referer:
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
        if "transfer" in referer:
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
            {"error": gettext("You do not have permission to view these groups.")}, status=403
        )

    submission_groups = SubmissionGroup.objects.filter(created_by=user_id)
    groups = [
        {"uuid": str(group.uuid), "name": group.name, "description": group.description}
        for group in submission_groups
    ]
    return JsonResponse(groups, safe=False)
