""" Views
"""

from json.decoder import JSONDecodeError
import logging
import threading

from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView, FormView
from formtools.wizard.views import SessionWizardView

from recordtransfer.appsettings import BAG_STORAGE_FOLDER
from recordtransfer.bagger import Bagger
from recordtransfer.caais import TagGenerator, DocumentGenerator
from recordtransfer.models import UploadedFile, UploadSession
from recordtransfer.persistentuploadhandler import PersistentUploadedFile


LOGGER = logging.getLogger(__name__)


class Index(TemplateView):
    template_name = 'recordtransfer/home.html'


class TransferSent(TemplateView):
    template_name = 'recordtransfer/transfersent.html'


class FormPreparation(TemplateView):
    template_name = 'recordtransfer/formpreparation.html'


class TransferFormWizard(SessionWizardView):
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
        context = super(TransferFormWizard, self).get_context_data(form, **kwargs)
        step_name = self.steps.current
        context.update({'form_title': self.TEMPLATES[step_name]['formtitle']})
        if 'infomessage' in self.TEMPLATES[step_name]:
            context.update({'info_message': self.TEMPLATES[step_name]['infomessage']})
        return context

    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()

        upload_session_token = data['session_token']

        files = UploadedFile.objects.filter(
            session__token=upload_session_token
        ).filter(
            old_copy_removed=False
        )

        caais_tags = TagGenerator.generate_tags_from_form(data)
        doc_generator = DocumentGenerator(caais_tags)
        html_document = doc_generator.generate_html_document()
        tag_objects = [
            (caais_tags, 'yaml'),
            (html_document, 'html'),
        ]
        LOGGER.info('Generated yaml metadata and html document')

        bagging_thread = threading.Thread(
            target=Bagger.create_bag,
            args=(BAG_STORAGE_FOLDER, upload_session_token, {}, tag_objects, True)
        )
        bagging_thread.setDaemon(True)
        bagging_thread.start()
        LOGGER.info('Starting bag creation in the background')

        return HttpResponseRedirect(reverse('recordtransfer:transfersent'))


def uploadfiles(request):
    """ Upload one or more files to the server, and return a list of all the files uploaded. The
    list contains the path to the uploaded file on the server, and the name of the file uploaded.
    """
    if not request.method == 'POST':
        return JsonResponse({'error': 'Files can only be uploaded using POST.'}, status=500)
    if not request.FILES:
        return JsonResponse({'files': []}, status=200)

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

        files_dictionary = request.FILES.dict()
        for key in files_dictionary:
            if not isinstance(files_dictionary[key], PersistentUploadedFile):
                return JsonResponse({
                    'error': "Development issue: Wrong file upload handler being used, check"
                    f" Django settings. Got file of type {type(files_dictionary[key]).__name__},"
                    "but expected PersistentUploadedFile.",
                }, status=500)

            file_path = files_dictionary[key].temporary_file_path()
            file_name = files_dictionary[key].name
            new_file = UploadedFile(name=file_name, path=file_path, old_copy_removed=False,
                                    session=session)
            new_file.save()

        return JsonResponse({'upload_session_token': session.token}, status=200)

    except Exception as exc:
        return JsonResponse({'error': f'Uncaught Exception:\n{str(exc)}'}, status=500)
