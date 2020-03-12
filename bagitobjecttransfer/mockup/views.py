from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView, FormView

import json
import os
import  threading
import logging

from .bagger import Bagger
from .forms import TransferForm
from .appsettings import BAG_STORAGE_FOLDER
from .persistentuploadhandler import PersistentUploadedFile


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

        file_list = []
        for key in files_dictionary:
            if not isinstance(files_dictionary[key], PersistentUploadedFile):
                return JsonResponse({
                    'error': "Development issue: Wrong file upload handler being used, check Django" \
                   f" settings. Got file of type {type(files_dictionary[key]).__name__}, but" \
                    " expected PersistentUploadedFile.",
                }, status=500)

            file_list.append({
                'filepath': files_dictionary[key].temporary_file_path(),
                'name': files_dictionary[key].name,
            })

        return JsonResponse({'files': file_list}, status=200)

    except Exception as e:
        return JsonResponse({'error': f'Uncaught Exception:\n{str(e)}'}, status=500)


def sendtransfer(request):
    if request.method == 'POST':
        try:
            form = TransferForm(request.POST)
            if form.is_valid():
                file_list_json = form.cleaned_data['file_list_json']

                # TODO: Don't trust this file list, make sure all of the files are somewhere safe
                # and someone isn't trying to access files somewhere else on disk.
                # TODO: Also, check that there is more than one file and that it's a list and that
                # all list items have filepath and name.
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

                # I'd like to re-populate the dropzone here instead but it may
                # not be possible, so I'm removing the files instead
                if form.data['file_list_json']:
                    files = json.loads(form.data['file_list_json'])
                    for f in files:
                        try:
                            os.remove(f['filepath'])
                        except FileNotFoundError:
                            pass

                return render(request, 'mockup/transfer.html', {'form': form})

        except KeyError:
            return render(request, 'mockup/transfer.html', {
                'error_msg': 'Transfer Failed, could not find form data in POST.'
            })
        else:
            return HttpResponseRedirect(reverse('mockup:transfersent'))
    else:
        form = TransferForm()
        return render(request, 'mockup/transfer.html', {'form': form})


def create_bag_background(storage_folder: str, files: list, metadata: dict):
    Bagger.create_bag(storage_folder, files, metadata)

    for f in files:
        try:
            os.remove(f['filepath'])
        except FileNotFoundError:
            logging.warn(f'Views: It appears that file {f["filepath"]} has already been removed')
