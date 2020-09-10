import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView
from formtools.wizard.views import SessionWizardView

from recordtransfer.models import UploadedFile, UploadSession, Bag
from recordtransfer.jobs import bag_user_metadata_and_files


LOGGER = logging.getLogger(__name__)


class Index(TemplateView):
    template_name = 'recordtransfer/home.html'


class TransferSent(TemplateView):
    template_name = 'recordtransfer/transfersent.html'


class FormPreparation(TemplateView):
    template_name = 'recordtransfer/formpreparation.html'


class UserProfile(TemplateView):
    template_name = 'recordtransfer/profile.html'


class About(TemplateView):
    template_name = 'recordtransfer/about.html'


class TransferFormWizard(SessionWizardView):
    ''' A form for collecting user metadata and uploading files '''

    TEMPLATES = {
        "sourceinfo": {
            "templateref": "recordtransfer/standardform.html",
            "formtitle": "Source Information",
        },
        "contactinfo": {
            "templateref": "recordtransfer/standardform.html",
            "formtitle": "Contact Information",
        },
        "recorddescription": {
            "templateref": "recordtransfer/standardform.html",
            "formtitle": "Record Description",
        },
        "rights": {
            "templateref": "recordtransfer/formsetform.html",
            "formtitle": "Record Rights",
        },
        "otheridentifiers": {
            "templateref": "recordtransfer/formsetform.html",
            "formtitle": "Other Identifiers",
            "infomessage": (
                "This step is optional, if you do not have any other IDs associated with the "
                "records, go to the next step"
            )
        },
        "uploadfiles": {
            "templateref": "recordtransfer/dropzoneform.html",
            "formtitle": "Upload Files",
        },
    }

    def get_template_names(self):
        step_name = self.steps.current
        return [self.TEMPLATES[step_name]["templateref"]]

    def get_context_data(self, form, **kwargs):
        ''' Send extra data variables to form templates '''
        context = super(TransferFormWizard, self).get_context_data(form, **kwargs)
        step_name = self.steps.current
        context.update({'form_title': self.TEMPLATES[step_name]['formtitle']})
        if 'infomessage' in self.TEMPLATES[step_name]:
            context.update({'info_message': self.TEMPLATES[step_name]['infomessage']})
        return context

    def done(self, form_list, **kwargs):
        ''' Retrieves all of the form data, and creates a bag from it '''
        form_data = self.get_all_cleaned_data()
        bag_user_metadata_and_files.delay(form_data, self.request.user)
        return HttpResponseRedirect(reverse('recordtransfer:transfersent'))


def uploadfiles(request):
    """ Upload one or more files to the server, and return a token representing the file upload
    session. If a token is passed in the request header using the Upload-Session-Token header, the
    uploaded files will be added to the corresponding session, meaning this endpoint can be hit
    multiple times for a large batch upload of files.
    """
    if not request.method == 'POST':
        return JsonResponse({'error': 'Files can only be uploaded using POST.'}, status=500)
    if not request.FILES:
        return JsonResponse({'upload_session_token': ''}, status=200)

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
            new_file = UploadedFile(name=temp_file.name, path=temp_file.path,
                old_copy_removed=False, session=session)
            new_file.save()

        return JsonResponse({'upload_session_token': session.token}, status=200)

    except Exception as exc:
        LOGGER.error('Uncaught exception in upload_file: %s' % str(exc))
        return JsonResponse({'error': f'Uncaught Exception:\n{str(exc)}'}, status=500)
