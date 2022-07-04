import datetime
import pickle
from typing import Union
import logging

import clamd
from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView, FormView, UpdateView
from formtools.wizard.views import SessionWizardView

from caais.models import RightsType, SourceRole, SourceType
from recordtransfer import settings
from recordtransfer.models import UploadedFile, UploadSession, User, BagGroup, Right, \
    SourceRole, SourceType, Submission, SavedTransfer
from recordtransfer.jobs import bag_user_metadata_and_files, send_user_activation_email
from recordtransfer.settings import CLAMAV_HOST, CLAMAV_PORT, CLAMAV_ENABLED, MAX_SAVED_TRANSFER_COUNT
from recordtransfer.utils import get_human_readable_file_count, get_human_readable_size
from recordtransfer.forms import SignUpForm, UserProfileForm
from recordtransfer.tokens import account_activation_token


LOGGER = logging.getLogger(__name__)


class Index(TemplateView):
    ''' The homepage '''
    template_name = 'recordtransfer/home.html'


class TransferSent(TemplateView):
    ''' The page a user sees when they finish a transfer '''
    template_name = 'recordtransfer/transfersent.html'


class SystemErrorPage(TemplateView):
    """ The page a user sees when there is some system error. """
    template_name = 'recordtransfer/systemerror.html'


class UserProfile(UpdateView):
    ''' This view shows two things:
    - The user's profile information
    - A list of the Bags a user has created via transfer
    '''

    template_name = 'recordtransfer/profile.html'
    paginate_by = 10
    form_class = UserProfileForm
    success_url = reverse_lazy('recordtransfer:userprofile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super(UserProfile, self).get_context_data(**kwargs)
        context['in_process_submissions'] = SavedTransfer.objects.filter(user=self.request.user)\
            .order_by('-last_updated')
        context['user_submissions'] = Submission.objects.filter(user=self.request.user).order_by('-submission_date')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Preferences updated')
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        if 'delete_transfer' in request.GET:
            transfers = SavedTransfer.objects.filter(
                user=self.request.user,
                id=request.GET.get('delete_transfer')
            )
            for transfer in transfers:
                transfer.delete()
        return super().get(request, *args, **kwargs)


class About(TemplateView):
    ''' About the application '''
    template_name = 'recordtransfer/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accepted_files'] = settings.ACCEPTED_FILE_FORMATS
        context['max_total_upload_size'] = settings.MAX_TOTAL_UPLOAD_SIZE
        context['max_single_upload_size'] = settings.MAX_SINGLE_UPLOAD_SIZE
        context['max_total_upload_count'] = settings.MAX_TOTAL_UPLOAD_COUNT
        return context


class ActivationSent(TemplateView):
    ''' The page a user sees after creating an account '''
    template_name = 'recordtransfer/activationsent.html'


class ActivationComplete(TemplateView):
    ''' The page a user sees when their account has been activated '''
    template_name = 'recordtransfer/activationcomplete.html'


class ActivationInvalid(TemplateView):
    ''' The page a user sees if their account could not be activated '''
    template_name = 'recordtransfer/activationinvalid.html'


class CreateAccount(FormView):
    ''' Allows a user to create a new account with the SignUpForm. When the form is submitted
    successfully, send an email to that user with a link that lets them activate their account.
    '''
    template_name = 'recordtransfer/signupform.html'
    form_class = SignUpForm
    success_url = reverse_lazy('recordtransfer:activationsent')

    def form_valid(self, form):
        new_user = form.save(commit=False)
        new_user.is_active = False
        new_user.gets_bag_email_updates = False
        new_user.save()
        send_user_activation_email.delay(new_user)
        return super().form_valid(form)


def activate_account(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.confirmed_email = True
        user.save()
        login(request, user)
        return HttpResponseRedirect(reverse('recordtransfer:accountcreated'))

    return HttpResponseRedirect(reverse('recordtransfer:activationinvalid'))


class TransferFormWizard(SessionWizardView):
    ''' A multi-page form for collecting user metadata and uploading files. Uses a form wizard. For
    more info, visit this link: https://django-formtools.readthedocs.io/en/latest/wizard.html
    '''

    _TEMPLATES = {
        "acceptlegal": {
            "templateref": "recordtransfer/transferform_legal.html",
            "formtitle": gettext("Legal Agreement"),
        },
        "contactinfo": {
            "templateref": "recordtransfer/transferform_standard.html",
            "formtitle": gettext("Contact Information"),
            "infomessage": gettext(
                "Enter your contact information in case you need to be contacted by one of our "
                "archivists regarding your transfer"
            )
        },
        "sourceinfo": {
            "templateref": "recordtransfer/transferform_sourceinfo.html",
            "formtitle": gettext("Source Information"),
            "infomessage": gettext(
                "Enter the info for the source of the records. The source is the person or entity "
                "that created the records or is holding the records at the moment. If this is you, "
                "put your own information in"
            )
        },
        "recorddescription": {
            "templateref": "recordtransfer/transferform_standard.html",
            "formtitle": gettext("Record Description"),
            "infomessage": gettext(
                "Provide a brief description of the records you're transferring"
            )
        },
        "rights": {
            "templateref": "recordtransfer/transferform_rights.html",
            "formtitle": gettext("Record Rights"),
            "infomessage": gettext(
                "Enter any associated rights that apply to the records. Add as many rights "
                "sections as you like using the + More button. You may enter another type of "
                "rights if the dropdown does not contain the type of rights you're looking for."
            )
        },
        "otheridentifiers": {
            "templateref": "recordtransfer/transferform_formset.html",
            "formtitle": gettext("Other Identifiers (Optional)"),
            "infomessage": gettext(
                "This step is optional, if you do not have any other IDs associated with the "
                "records, go to the next step"
            )
        },
        "grouptransfer": {
            "templateref": "recordtransfer/transferform_group.html",
            "formtitle": gettext("Assign Transfer to Group (Optional)"),
            "infomessage": gettext(
                "If this transfer belongs in a group with other transfers you have made or will "
                "make, select the group it belongs in in the dropdown below, or create a new group"
            )
        },
        "uploadfiles": {
            "templateref": "recordtransfer/transferform_dropzone.html",
            "formtitle": gettext("Upload Files"),
            "infomessage": gettext(
                "Add any final notes you would like to add, and upload your files"
            )
        },
    }

    def get(self, request, *args, **kwargs):
        if self.steps.current == 'acceptlegal' and CLAMAV_ENABLED:
            clamd_socket = clamd.ClamdNetworkSocket(CLAMAV_HOST, CLAMAV_PORT)
            try:
                clamd_socket.ping()
            except clamd.ClamdError as exc:
                LOGGER.error("Unable to ping ClamAV", exc_info=exc)
                return HttpResponseRedirect(reverse('recordtransfer:systemerror'))
        resume_id = request.GET.get('resume_transfer', None)
        if resume_id:
            transfer = SavedTransfer.objects.filter(user=self.request.user, id=resume_id).first()
            if transfer is None:
                LOGGER.error(
                    f"Expected at least 1 saved transfers for user {self.request.user} and ID {resume_id}, found 0"
                )
            else:
                self.storage.data = pickle.loads(transfer.step_data)['past']
                self.storage.current_step = transfer.current_step
                return self.render(self.get_form())
        return super().get(self, request, *args, **kwargs)

    def post(self, *args, **kwargs):
        save_form_step = self.request.POST.get('save_form_step', None)
        if save_form_step and save_form_step in self.steps.all:
            resume_id = self.request.GET.get('resume_transfer', None)
            if resume_id:
                transfer = SavedTransfer.objects.filter(user=self.request.user, id=resume_id).first()
            else:
                transfer = SavedTransfer()
            transfer.current_step = save_form_step
            # Make a dict of form element names to values to store. Elements are prefixed with "<step_name>-"
            current_data = {f.replace(save_form_step + "-", ""): self.request.POST[f] for f in self.request.POST.keys()
                            if f.startswith(save_form_step + "-")}
            transfer.user = self.request.user
            transfer.last_updated = datetime.datetime.now(timezone.get_current_timezone())
            transfer.step_data = pickle.dumps({'past': self.storage.data, 'current': current_data })
            transfer.save()
            return redirect('recordtransfer:userprofile')
        else:
            return super().post(*args, **kwargs)

    def get_template_names(self):
        ''' Retrieve the name of the template for the current step '''
        step_name = self.steps.current
        return [self._TEMPLATES[step_name]["templateref"]]

    def get_form_initial(self, step):
        initial = self.initial_dict.get(step, {})
        resume_id = self.request.GET.get('resume_transfer', None)
        if resume_id is not None:
            transfer = SavedTransfer.objects.filter(user=self.request.user, id=resume_id).first()
            if step == transfer.current_step:
                data = pickle.loads(transfer.step_data)['current']
                for (k, v) in data.items():
                    initial[k] = v
        if step == 'contactinfo':
            curr_user = self.request.user
            initial['contact_name'] = f'{curr_user.first_name} {curr_user.last_name}'
            initial['email'] = str(curr_user.email)
        return initial

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == 'grouptransfer':
            users_groups = BagGroup.objects.filter(created_by=self.request.user)
            kwargs['users_groups'] = users_groups
        return kwargs

    def get_context_data(self, form, **kwargs):
        ''' Retrieve context data for the current form template.

        Args:
            form: The form to display to the user.

        Returns:
            dict: A dictionary of context data to be used to render the form template.
        '''
        context = super().get_context_data(form, **kwargs)
        step_name = self.steps.current
        context.update({'form_title': self._TEMPLATES[step_name]['formtitle']})
        if 'infomessage' in self._TEMPLATES[step_name]:
            context.update({'info_message': self._TEMPLATES[step_name]['infomessage']})
        if step_name == 'grouptransfer':
            users_groups = BagGroup.objects.filter(created_by=self.request.user)
            context.update({'users_groups': users_groups})
        elif step_name == 'rights':
            all_rights = RightsType.objects.all().exclude(name='Other')
            context.update({'rights': all_rights})
        elif step_name == 'sourceinfo':
            all_roles = SourceRole.objects.all().exclude(name='Other')
            all_types = SourceType.objects.all().exclude(name='Other')
            context.update({
                'source_roles': all_roles,
                'source_types': all_types,
            })
        resume_id = self.request.GET.get('resume_transfer', None)
        max_saves = SavedTransfer.objects.filter(user=self.request.user).count()
        if MAX_SAVED_TRANSFER_COUNT == 0:
            # If MAX_SAVED_TRANSFER_COUNT is 0, then don't show the save form button.
            save_form_state = 'off'
        elif resume_id is None and max_saves >= MAX_SAVED_TRANSFER_COUNT:
            # if the count of saved transfers is equal to or more than the maximum and we are NOT editing an existing
            # transfer, disable the save form button.
            save_form_state = 'disabled'
        else:
            # else enable the button.
            save_form_state = 'on'
        context.update({'save_form_state': save_form_state})
        return context

    def get_all_cleaned_data(self):
        cleaned_data = super().get_all_cleaned_data()

        # Get quantity and type of files for extent
        session = UploadSession.objects.filter(token=cleaned_data['session_token']).first()
        size = get_human_readable_size(session.upload_size, base=1024, precision=2)
        count = get_human_readable_file_count(
            [f.name for f in session.get_existing_file_set()],
            settings.ACCEPTED_FILE_FORMATS,
            LOGGER
        )

        cleaned_data['quantity_and_type_of_units'] = '{0}, totalling {1}'.format(count, size)

        start_date = cleaned_data['start_date_of_material']
        end_date = cleaned_data['end_date_of_material']
        if settings.USE_DATE_WIDGETS:
            # Convert the four date-related fields to a single date
            start_date = start_date.strftime(r'%Y-%m-%d')
            end_date = end_date.strftime(r'%Y-%m-%d')
            if cleaned_data['start_date_is_approximate']:
                start_date = settings.APPROXIMATE_DATE_FORMAT.format(date=start_date)
            if cleaned_data['end_date_is_approximate']:
                end_date = settings.APPROXIMATE_DATE_FORMAT.format(date=end_date)

        date_of_material = start_date if start_date == end_date else f'{start_date} - {end_date}'
        cleaned_data['date_of_material'] = date_of_material
        cleaned_data = TransferFormWizard.delete_keys(cleaned_data, [
            'start_date_is_approximate',
            'start_date_of_material',
            'start_date_of_material_text',
            'end_date_is_approximate',
            'end_date_of_material',
            'end_date_of_material_text'
        ])

        # Add dates for events
        current_time = timezone.localtime(timezone.now()).strftime(r'%Y-%m-%d %H:%M:%S %Z')
        cleaned_data['action_date'] = current_time
        cleaned_data['event_date'] = current_time

        return cleaned_data

    @staticmethod
    def delete_keys(form_data, keys):
        for key in keys:
            if key in form_data:
                del form_data[key]
        return form_data

    def done(self, form_list, **kwargs):
        ''' Retrieves all of the form data, and creates a bag from it asynchronously.

        Args:
            form_list: The list of forms the user filled out.

        Returns:
            HttpResponseRedirect: Redirects the user to the Transfer Sent page.
        '''
        form_data = self.get_all_cleaned_data()
        bag_user_metadata_and_files.delay(form_data, self.request.user)
        return HttpResponseRedirect(reverse('recordtransfer:transfersent'))


@require_http_methods(['POST'])
def uploadfiles(request):
    ''' Upload one or more files to the server, and return a token representing the file upload
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
    '''
    if not request.FILES:
        return JsonResponse({
            'error': gettext('No files were uploaded'),
            'verboseError': gettext('No files were uploaded'),
        }, status=400)

    try:
        headers = request.headers
        if not 'Upload-Session-Token' in headers or not headers['Upload-Session-Token']:
            session = UploadSession.new_session()
            session.save()
        else:
            session = UploadSession.objects.filter(token=headers['Upload-Session-Token']).first()
            if session is None:
                session = UploadSession.new_session()
                session.save()

        issues = []
        for _file in request.FILES.dict().values():
            file_check = _accept_file(_file.name, _file.size)
            if not file_check['accepted']:
                _file.close()
                issues.append({'file': _file.name, **file_check})
                continue

            session_check = _accept_session(_file.name, _file.size, session)
            if not session_check['accepted']:
                _file.close()
                issues.append({'file': _file.name, **session_check})
                continue

            try:
                content_check = _accept_contents(_file)
                if not content_check['accepted']:
                    _file.close()
                    issues.append({'file': _file.name, **content_check})
                    continue
            except clamd.ClamdError as exc:
                LOGGER.error("Unable to scan file (%s)", uploadfiles, exc_info=exc)
                session.remove_session_uploads()
                return JsonResponse(
                    {'uploadSessionToken': session.token,
                     'error': gettext('500 Internal Server Error'),
                     'verboseError': gettext('500 Internal Server Error'),
                     'fatalError': True,
                     'redirect': reverse('recordtransfer:systemerror')
                     }, status=500
                )

            new_file = UploadedFile(session=session, file_upload=_file, name=_file.name)
            new_file.save()

        return JsonResponse({'uploadSessionToken': session.token, 'issues': issues}, status=200)

    except Exception as exc:
        LOGGER.error(msg=('Uncaught exception in uploadfiles view: {0}'.format(str(exc))))
        return JsonResponse({
            'error': gettext('500 Internal Server Error'),
            'verboseError': gettext('500 Internal Server Error'),
        }, status=500)


@require_http_methods(['GET', 'POST'])
def accept_file(request):
    ''' Check whether the file is allowed to be uploaded by inspecting the file's extension. The
    allowed file extensions are set using the ACCEPTED_FILE_FORMATS setting.

    Args:
        request: The request sent by the user. This request should either be a GET or a POST
            request, with the name of the file in the **filename** parameter.

    Returns:
        JsonResponse: If the file is allowed to be uploaded, 'accepted' will be True. Otherwise,
            'accepted' is False and both 'error' and 'verboseError' are set.
    '''
    # Ensure required parameters are set
    request_params = request.POST if request.method == 'POST' else request.GET
    for required in ('filename', 'filesize'):
        if required not in request_params:
            return JsonResponse({
                'accepted': False,
                'error': gettext('Could not find {0} parameter in request').format(
                    required
                )
            }, status=400)
        if not request_params[required]:
            return JsonResponse({
                'accepted': False,
                'error': gettext('{0} parameter cannot be empty').format(
                    required
                )
            }, status=400)

    filename = request_params['filename']
    filesize = request_params['filesize']
    token = request.headers.get('Upload-Session-Token', None)

    try:
        file_check = _accept_file(filename, filesize)
        if not file_check['accepted']:
            return JsonResponse(file_check, status=200)

        if token:
            session = UploadSession.objects.filter(token=token).first()
            if session:
                session_check = _accept_session(filename, filesize, session)
                if not session_check['accepted']:
                    return JsonResponse(session_check, status=200)

        # The contents of the file are not known here, so it is not necessary to
        # call _accept_content()

        return JsonResponse({'accepted': True}, status=200)

    except Exception as exc:
        LOGGER.error(msg=('Uncaught exception in checkfile view: {0}'.format(str(exc))))
        return JsonResponse({
            'accepted': False,
            'error': gettext('500 Internal Server Error'),
            'verboseError': gettext('500 Internal Server Error'),
        }, status=500)


def _accept_file(filename: str, filesize: Union[str, int]) -> dict:
    ''' Determine if a new file should be accepted. Does not check the file's
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
    '''
    mib_to_bytes = lambda m: m * (1024 ** 2)
    bytes_to_mib = lambda b: b / (1024 ** 2)

    # Check extension exists
    name_split = filename.split('.')
    if len(name_split) == 1:
        return {
            'accepted': False,
            'error': gettext('File is missing an extension.'),
            'verboseError': gettext(
                'The file "{0}" does not have a file extension'
            ).format(filename)
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
            'accepted': False,
            'error': gettext(
                'Files with "{0}" extension are not allowed.'
            ).format(extension),
            'verboseError': gettext(
                'The file "{0}" has an invalid extension (.{1})'
            ).format(filename, extension)
        }

    # Check filesize is an integer
    size = filesize
    try:
        size = int(filesize)
        if size < 0:
            raise ValueError('File size cannot be negative')
    except ValueError:
        return {
            'accepted': False,
            'error': gettext('File size is invalid.'),
            'verboseError': gettext(
                'The file "{0}" has an invalid size ({1})'
            ).format(filename, size)
        }

    # Check file has some contents (i.e., non-zero size)
    if size == 0:
        return {
            'accepted': False,
            'error': gettext('File is empty.'),
            'verboseError': gettext('The file "{0}" is empty').format(filename)
        }

    # Check file size is less than the maximum allowed size for a single file
    max_single_size = min(settings.MAX_SINGLE_UPLOAD_SIZE, settings.MAX_TOTAL_UPLOAD_SIZE)
    max_single_size_bytes = mib_to_bytes(max_single_size)
    size_mib = bytes_to_mib(size)
    if size > max_single_size_bytes:
        return {
            'accepted': False,
            'error': gettext(
                'File is too big ({0:.2f}MiB). Max filesize: {1}MiB'
            ).format(size_mib, max_single_size),
            'verboseError': gettext(
                'The file "{0}" is too big ({1:.2f}MiB). Max filesize: {2}MiB'
            ).format(filename, size_mib, max_single_size),
        }

    # All checks succeded
    return {'accepted': True}


def _accept_session(filename: str, filesize: Union[str, int], session: UploadSession) -> dict:
    ''' Determine if a new file should be accepted as part of the session.

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
    '''
    if not session:
        return {'accepted': True}

    mib_to_bytes = lambda m: m * (1024 ** 2)

    # Check number of files is within allowed total
    if session.number_of_files_uploaded() >= settings.MAX_TOTAL_UPLOAD_COUNT:
        return {
            'accepted': False,
            'error': gettext('You can not upload anymore files.'),
            'verboseError': gettext(
                'The file "{0}" would push the total file count past the '
                'maximum number of files ({1})'
            ).format(filename, settings.MAX_TOTAL_UPLOAD_SIZE)
        }

    # Check total size of all files plus current one is within allowed size
    max_size = max(settings.MAX_SINGLE_UPLOAD_SIZE, settings.MAX_TOTAL_UPLOAD_SIZE)
    max_remaining_size_bytes = mib_to_bytes(max_size) - session.upload_size
    if int(filesize) > max_remaining_size_bytes:
        return {
            'accepted': False,
            'error': gettext(
                'Maximum total upload size ({0} MiB) exceeded'
            ).format(max_size),
            'verboseError': gettext(
                'The file "{0}" would push the total transfer size past the '
                '{1}MiB max'
            ).format(filename, max_size)
        }

    # Check that a file with this name has not already been uploaded
    filename_list = session.uploadedfile_set.all().values_list('name', flat=True)
    if filename in filename_list:
        return {
            'accepted': False,
            'error': gettext(
                'A file with the same name has already been uploaded.'
            ),
            'verboseError': gettext(
                'A file with the name "{0}" has already been uploaded'
            ).format(filename)
        }

    # All checks succeded
    return {'accepted': True}


def _accept_contents(file_upload):
    ''' Scan the contents of the file to ensure it does not contain malware.

    Args:
        file_upload: File object from request.FILES

    Returns:
        (dict): A dictionary containing an 'accepted' key that contains True if
            the file did not contain malware, or False if not. The dictionary
            also contains an 'error', 'verboseError', and 'clamav' key if
            accepted is False. The 'clamav' key is a dict itself that has a
            'reason' and a 'status' key.
    '''
    if CLAMAV_ENABLED:
        clamd_socket = clamd.ClamdNetworkSocket(CLAMAV_HOST, CLAMAV_PORT)
        scan_results = clamd_socket.instream(file_upload.file)
        status, reason = scan_results['stream']
        if status != 'OK':
            return {
                'accepted': False,
                'error': 'Malware found in file',
                'verboseError': gettext(
                    'The file "{0}" was identified to contain malware! This issue '
                    'will be sent to the administrator'.format(file_upload)
                ),
                'clamav': {
                    'reason': reason,
                    'status': status,
                }
            }
    return {'accepted': True}
