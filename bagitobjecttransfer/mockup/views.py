from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView, FormView

from .forms import TransferForm
from .appsettings import bag_storage_folder

from .bagger import Bagger


class Index(TemplateView):
    template_name = 'mockup/home.html'


class Transfer(FormView):
    template_name = 'mockup/transfer.html'
    form_class = TransferForm


class TransferSent(TemplateView):
    template_name = 'mockup/transfersent.html'


def uploadfiles(request):
    files_dictionary = request.FILES.dict()

    for key in files_dictionary:
        print ({
            'filepath': files_dictionary[key].temporary_file_path(),
            'name': files_dictionary[key].name
        })

    return JsonResponse({'success': True}, status=200)


def sendtransfer(request):
    if request.method == 'POST':
        try:
            form = TransferForm(request.POST)
            if form.is_valid():
                '''
                files = request.FILES.getlist('upload_files')
                file_list = []
                for f in files:
                    file_list.append({
                        'filepath': f.temporary_file_path(),
                        'name': f.name
                    })
                '''

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

                # Bagger.create_bag(bag_storage_folder, [], metadata)

            else:
                for err in form.errors:
                    for message in form.errors[err]:
                        print (f'{err} Error: {message}')

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
