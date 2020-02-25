from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView


class Index(TemplateView):
    template_name = 'mockup/home.html'


class Transfer(TemplateView):
    template_name = 'mockup/transfer.html'


class TransferSent(TemplateView):
    template_name = 'mockup/transfersent.html'


def sendtransfer(request):
    if request.method == 'POST':
        try:
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            print (f'First Name: {first_name} | Last Name: {last_name}')
        except KeyError:
            return render(request, 'mockup/transfer.html', {
                'error_msg': 'Transfer Failed, could not find form data in POST.'
            })
        else:
            return HttpResponseRedirect(reverse('mockup:transfersent'))
    else:
        return render(request, 'mockup/transfer.html')
