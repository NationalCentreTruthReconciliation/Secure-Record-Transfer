from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView, FormView

from json.decoder import JSONDecodeError
import json
import logging
import os
import threading

from mockup.appsettings import BAG_STORAGE_FOLDER
from mockup.bagger import Bagger
from mockup.forms import TransferForm
from mockup.models import UploadedFile, UploadSession
from mockup.persistentuploadhandler import PersistentUploadedFile


logger = logging.getLogger('mockup')


class Index(TemplateView):
    template_name = 'mockup/home.html'


class Transfer(FormView):
    template_name = 'mockup/transfer.html'
    form_class = TransferForm


class TransferSent(TemplateView):
    template_name = 'mockup/transfersent.html'


def uploadfiles(request):
    """ Upload one or more files to the server, and return a list of all the files uploaded. The
    list contains the path to the uploaded file on the server, and the name of the file uploaded.
    """
    if not request.method == 'POST':
        return JsonResponse({'error': 'Files can only be uploaded using POST.'}, status=500)
    if not request.FILES:
        return JsonResponse({'files': []}, status=200)

    try:
        files_dictionary = request.FILES.dict()

        session = UploadSession()
        session.save()

        for key in files_dictionary:
            if not isinstance(files_dictionary[key], PersistentUploadedFile):
                return JsonResponse({
                    'error': "Development issue: Wrong file upload handler being used, check Django" \
                   f" settings. Got file of type {type(files_dictionary[key]).__name__}, but" \
                    " expected PersistentUploadedFile.",
                }, status=500)

            file_path = files_dictionary[key].temporary_file_path()
            file_name = files_dictionary[key].name
            new_file = UploadedFile(name=file_name, path=file_path, old_copy_removed=False, session=session)
            new_file.save()

        return JsonResponse({'upload_session_token': session.token}, status=200)

    except Exception as e:
        return JsonResponse({'error': f'Uncaught Exception:\n{str(e)}'}, status=500)


def sendtransfer(request):
    if request.method == 'POST':
        try:
            form = TransferForm(request.POST)
            if form.is_valid():
                file_list_json = form.cleaned_data['file_list_json']
                uploaded_files = json.loads(file_list_json)
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
                logger.info('Views: Starting bag creation in the background')
                bagging_thread = threading.Thread(
                    target=create_bag_background,
                    args=(BAG_STORAGE_FOLDER, uploaded_files, metadata)
                )
                bagging_thread.setDaemon(True)
                bagging_thread.start()

            else:
                for err in form.errors:
                    for message in form.errors[err]:
                        print (f'{err} Error: {message}')

                if form.data['file_list_json']:
                    files = json.loads(form.data['file_list_json'])
                    remove_file_list(files)

                return render(request, 'mockup/transfer.html', {'form': form})
        except JSONDecodeError as e:
            print(f'JSONDecodeError: {e}')
            return render(request, 'mockup/transfer.html', {'form': form})
        except KeyError as e:
            print(f'KeyError: {e}')
            return render(request, 'mockup/transfer.html', {'form': form})
        else:
            return HttpResponseRedirect(reverse('mockup:transfersent'))
    else:
        form = TransferForm()
        return render(request, 'mockup/transfer.html', {'form': form})


def remove_file_list(file_list: list):
    for f in file_list:
        try:
            os.remove(f['filepath'])
        except FileNotFoundError:
            pass


def create_bag_background(storage_folder: str, files: list, metadata: dict):
    Bagger.create_bag(storage_folder, files, metadata)

    for f in files:
        try:
            os.remove(f['filepath'])
        except FileNotFoundError:
            logging.warn(f'Views: It appears that file {f["filepath"]} has already been removed')
