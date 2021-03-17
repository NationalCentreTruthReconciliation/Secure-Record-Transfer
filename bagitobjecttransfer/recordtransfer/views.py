import logging
from pathlib import Path

from django.contrib.auth import login
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext
from django.views.generic import TemplateView, FormView, ListView
from formtools.wizard.views import SessionWizardView

from recordtransfer.models import UploadedFile, UploadSession, User, Bag, BagGroup
from recordtransfer.jobs import bag_user_metadata_and_files, send_user_activation_email
from recordtransfer.settings import ACCEPTED_FILE_FORMATS, APPROXIMATE_DATE_FORMAT
from recordtransfer.utils import get_human_readable_file_count
from recordtransfer.forms import SignUpForm
from recordtransfer.tokens import account_activation_token


LOGGER = logging.getLogger(__name__)


class Index(TemplateView):
    ''' The homepage '''
    template_name = 'recordtransfer/home.html'


class TransferSent(TemplateView):
    ''' The page a user sees when they finish a transfer '''
    template_name = 'recordtransfer/transfersent.html'


class FormPreparation(TemplateView):
    ''' The page a user sees before they start a transfer '''
    template_name = 'recordtransfer/formpreparation.html'


class UserProfile(ListView):
    ''' This view shows two things:
    - The user's profile information
    - A list of the Bags a user has created via transfer
    '''

    template_name = 'recordtransfer/profile.html'
    context_object_name = 'user_bags'
    model = Bag
    paginate_by = 10

    def get_queryset(self):
        return Bag.objects.filter(user=self.request.user).order_by('-bagging_date')


class About(TemplateView):
    ''' About the application '''
    template_name = 'recordtransfer/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accepted_files'] = ACCEPTED_FILE_FORMATS
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
            "templateref": "recordtransfer/transferform_formset.html",
            "formtitle": gettext("Record Rights"),
            "infomessage": gettext(
                "Enter any associated rights that apply to the records. They can be copyright, "
                "intellectual property, cultural rights, etc. Add as many rights sections as you "
                "like using the + More button"
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

    def get_template_names(self):
        ''' Retrieve the name of the template for the current step '''
        step_name = self.steps.current
        return [self._TEMPLATES[step_name]["templateref"]]

    def get_form_initial(self, step):
        initial = self.initial_dict.get(step, {})
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
        return context

    def get_all_cleaned_data(self):
        cleaned_data = super().get_all_cleaned_data()

        # Get quantity and type of files for extent
        file_names = list(map(str, UploadedFile.objects.filter(
            session__token=cleaned_data['session_token']
        ).filter(
            old_copy_removed=False
        ).values_list('name', flat=True)))

        cleaned_data['quantity_and_type_of_units'] = get_human_readable_file_count(file_names,
            ACCEPTED_FILE_FORMATS)

        # Convert the four date-related fields to a single date
        start_date = cleaned_data['start_date_of_material'].strftime(r'%Y-%m-%d')
        end_date = cleaned_data['end_date_of_material'].strftime(r'%Y-%m-%d')
        if cleaned_data['start_date_is_approximate']:
            start_date = APPROXIMATE_DATE_FORMAT.format(date=start_date)
        if cleaned_data['end_date_is_approximate']:
            end_date = APPROXIMATE_DATE_FORMAT.format(date=end_date)

        date_of_material = start_date if start_date == end_date else f'{start_date} - {end_date}'
        cleaned_data['date_of_material'] = date_of_material
        del cleaned_data['start_date_is_approximate']
        del cleaned_data['start_date_of_material']
        del cleaned_data['end_date_is_approximate']
        del cleaned_data['end_date_of_material']

        # Add dates for events
        current_time = timezone.now().strftime(r'%Y-%m-%d %H:%M:%S %Z')
        cleaned_data['action_date'] = current_time
        cleaned_data['event_date'] = current_time

        return cleaned_data

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


def uploadfiles(request):
    ''' Upload one or more files to the server, and return a token representing the file upload
    session. If a token is passed in the request header using the Upload-Session-Token header, the
    uploaded files will be added to the corresponding session, meaning this endpoint can be hit
    multiple times for a large batch upload of files.

    Each file type is checked against this application's ACCEPTED_FILE_FORMATS setting, if any
    file is not an accepted type, a 403 status is returned.

    Args:
        request: The request sent by the user.

    Returns:
        JsonResponse: If the upload was successful, the session token is returned in
        upload_session_token. If not successful, the error description is returned in 'error',
            and a more verbose error is returned in 'verboseError'.
    '''
    if not request.method == 'POST':
        terse_error = gettext('Files can only be uploaded using POST.')
        verbose_error =  gettext(('Attempted to uploaded files using the {0} HTTP method, but '
                                  'only POST is allowed.').format(request.method))
        return JsonResponse({
            'error': terse_error,
            'verboseError': verbose_error,
        }, status=403)

    if not request.FILES:
        return JsonResponse({
            'error': gettext('No files were uploaded'),
            'verboseError': gettext('No files were uploaded'),
        }, status=403)

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

        for _, temp_file in request.FILES.dict().items():
            file_accepted = False
            temp_file_extension = Path(temp_file.name).suffix.lower().replace('.', '')
            for _, accepted_extensions in ACCEPTED_FILE_FORMATS.items():
                if temp_file_extension in accepted_extensions:
                    file_accepted = True
                    break

            if not file_accepted:
                terse_error = gettext('{0} files are not allowed'.format(temp_file_extension))
                verbose_error = gettext('{0} file has an unaccepted format ({1}).'.format(
                    temp_file_extension, temp_file.name))
                return JsonResponse({
                        'error': terse_error,
                        'verboseError': verbose_error,
                    }, status=403)

            new_file = UploadedFile(name=temp_file.name, path=temp_file.path,
                old_copy_removed=False, session=session)
            new_file.save()

        return JsonResponse({'upload_session_token': session.token}, status=200)

    except Exception as exc:
        LOGGER.error(msg=('Uncaught exception in uploadfiles view: {0}'.format(str(exc))))
        return JsonResponse({
            'error': gettext('500 Internal Server Error'),
            'verboseError': gettext('500 Internal Server Error'),
        }, status=500)
