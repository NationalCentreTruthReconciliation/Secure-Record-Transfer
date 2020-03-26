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

from mockup.appsettings import BAG_STORAGE_FOLDER
from mockup.bagger import Bagger
from mockup.models import UploadedFile, UploadSession
from mockup.persistentuploadhandler import PersistentUploadedFile


LOGGER = logging.getLogger(__name__)


class Index(TemplateView):
    template_name = 'mockup/home.html'


class TransferSent(TemplateView):
    template_name = 'mockup/transfersent.html'


class TransferFormWizard(SessionWizardView):
    TEMPLATES = {
        "sourceinfo": {
            "templateref": "mockup/standardform.html",
            "formtitle": "Source Information",
        },
        "contactinfo": {
            "templateref": "mockup/standardform.html",
            "formtitle": "Contact Information",
        },
        "recorddescription": {
            "templateref": "mockup/standardform.html",
            "formtitle": "Record Description",
        },
        "uploadfiles": {
            "templateref": "mockup/dropzoneform.html",
            "formtitle": "Upload Files"
        }
    }

    def get_template_names(self):
        step_name = self.steps.current
        return [self.TEMPLATES[step_name]["templateref"]]

    def get_context_data(self, form, **kwargs):
        context = super(TransferFormWizard, self).get_context_data(form, **kwargs)
        step_name = self.steps.current
        context.update({'form_title': self.TEMPLATES[step_name]["formtitle"]})
        return context

    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()

        files = UploadedFile.objects.filter(
            session__token=data['session_token']
        ).filter(
            old_copy_removed=False
        )

        for upload in files:
            upload.delete_file()

        return HttpResponseRedirect(reverse('mockup:transfersent'))


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


'''
def sendtransfer(request):
    """ Send a completed transfer form to the server.
    """
    if request.method == 'POST':
        try:
            form = TransferForm(request.POST)
            if form.is_valid():
                session_token = form.cleaned_data['session_token']
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                metadata = {
                    'Contact-Name': f'{first_name} {last_name}',
                    'Contact-Phone': form.cleaned_data['phone_number'],
                    'Contact-Email': form.cleaned_data['email'],
                    'Source-Organization': form.cleaned_data['organization'],
                    'Organization-Address': form.cleaned_data['organization_address'],
                    'External-Description': form.cleaned_data['description'],
                }
                LOGGER.info('Starting bag creation in the background')
                bagging_thread = threading.Thread(
                    target=Bagger.create_bag,
                    args=(BAG_STORAGE_FOLDER, session_token, metadata, True)
                )
                bagging_thread.setDaemon(True)
                bagging_thread.start()

            else:
                for err in form.errors:
                    for message in form.errors[err]:
                        print(f'{err} Error: {message}')

                if form.data['session_token']:
                    uploaded_files = UploadedFile.objects.filter(
                        session__token=form.data['session_token'])
                    for upload in uploaded_files:
                        upload.delete_file()

                return render(request, 'mockup/transfer.html', {'form': form})
        except JSONDecodeError as exc:
            print(f'JSONDecodeError: {exc}')
            return render(request, 'mockup/transfer.html', {'form': form})
        except KeyError as exc:
            print(f'KeyError: {exc}')
            return render(request, 'mockup/transfer.html', {'form': form})
        else:
            return HttpResponseRedirect(reverse('mockup:transfersent'))
    else:
        form = TransferForm()
        return render(request, 'mockup/transfer.html', {'form': form})
'''
