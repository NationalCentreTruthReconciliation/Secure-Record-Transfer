from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView, FormView

from .forms import TransferForm

class Index(TemplateView):
    template_name = 'mockup/home.html'


class Transfer(FormView):
    template_name = 'mockup/transfer.html'
    form_class = TransferForm


class TransferSent(TemplateView):
    template_name = 'mockup/transfersent.html'


def sendtransfer(request):
    if request.method == 'POST':
        try:
            form = TransferForm(request.POST)
            if form.is_valid():
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                print (f'First Name: {first_name} | Last Name: {last_name}')
            else:
                print ('Form was invalid...')
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
