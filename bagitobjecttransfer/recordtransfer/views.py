import logging
from pathlib import Path

from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext
from django.views.generic import TemplateView
from formtools.wizard.views import SessionWizardView

from recordtransfer.models import UploadedFile, UploadSession
from recordtransfer.jobs import bag_user_metadata_and_files
from recordtransfer.settings import ACCEPTED_FILE_FORMATS, APPROXIMATE_DATE_FORMAT
from recordtransfer.filecounter import get_human_readable_file_count


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


class UserProfile(TemplateView):
    ''' A page for a user to see and edit their information '''
    template_name = 'recordtransfer/profile.html'


class About(TemplateView):
    ''' About the application '''
    template_name = 'recordtransfer/about.html'


class TransferFormWizard(SessionWizardView):
    ''' A multi-page form for collecting user metadata and uploading files. Uses a form wizard. For
    more info, visit this link: https://django-formtools.readthedocs.io/en/latest/wizard.html
    '''

    _TEMPLATES = {
        "sourceinfo": {
            "templateref": "recordtransfer/standardform.html",
            "formtitle": gettext("Source Information"),
            "infomessage": gettext(
                "Enter the info for the source of the records"
            )
        },
        "contactinfo": {
            "templateref": "recordtransfer/standardform.html",
            "formtitle": gettext("Contact Information"),
            "infomessage": gettext(
                "Enter your contact information in case you need to be contacted by one of our "
                "archivists regarding your transfer"
            )
        },
        "recorddescription": {
            "templateref": "recordtransfer/standardform.html",
            "formtitle": gettext("Record Description"),
            "infomessage": gettext(
                "Provide a brief description of the records you're transferring"
            )
        },
        "rights": {
            "templateref": "recordtransfer/formsetform.html",
            "formtitle": gettext("Record Rights"),
            "infomessage": gettext(
                "Enter any associated rights that apply to the records. They can be copyright, "
                "intellectual property, cultural rights, etc. Add as many rights sections as you "
                "like using the + More button"
            )
        },
        "otheridentifiers": {
            "templateref": "recordtransfer/formsetform.html",
            "formtitle": gettext("Other Identifiers"),
            "infomessage": gettext(
                "This step is optional, if you do not have any other IDs associated with the "
                "records, go to the next step"
            )
        },
        "uploadfiles": {
            "templateref": "recordtransfer/dropzoneform.html",
            "formtitle": gettext("Upload Files"),
            "infomessage": gettext(
                "Upload the files you intend to transfer to the NCTR"
            )
        },
    }

    def get_template_names(self):
        ''' Retrieve the name of the template for the current step '''
        step_name = self.steps.current
        return [self._TEMPLATES[step_name]["templateref"]]

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
    ''' Upload one or more files to the server, and return a token representing the file upload \
    session. If a token is passed in the request header using the Upload-Session-Token header, the \
    uploaded files will be added to the corresponding session, meaning this endpoint can be hit \
    multiple times for a large batch upload of files. \

    Each file type is checked against this application's ACCEPTED_FILE_FORMATS setting, if any \
    file is not an accepted type, a 403 status is returned.

    Args:
        request: The request sent by the user.

    Returns:
        JsonResponse: If the upload was successful, the session token is returned in \
        upload_session_token. If not successful, the error description is returned in 'error', \
        and a more verbose error is returned in 'verboseError'.
    '''
    if not request.method == 'POST':
        terse_error = gettext('Files can only be uploaded using POST.')
        verbose_error =  gettext('Attempted to uploaded files using the {method} HTTP method, but '
                                 'only POST is allowed.') % {'method': request.method}
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
                terse_error = gettext('{extension} files are not allowed') % \
                    {'extension': temp_file_extension}
                verbose_error = gettext('{name} file has an unaccepted format ({extension}).') % \
                    {'extension': temp_file_extension, 'name': temp_file.name}
                return JsonResponse({
                        'error': terse_error,
                        'verboseError': verbose_error,
                    }, status=403)

            new_file = UploadedFile(name=temp_file.name, path=temp_file.path,
                old_copy_removed=False, session=session)
            new_file.save()

        return JsonResponse({'upload_session_token': session.token}, status=200)

    except Exception as exc:
        LOGGER.error(msg=('Uncaught exception in upload_file: %s' % str(exc)))
        exc_msg = {'exc': str(exc)}
        return JsonResponse({
            'error': gettext('Server Error:\n{exc}') % exc_msg,
            'verboseError': gettext('The following exception was not caught:\n{exc}') % exc_msg,
        }, status=500)
