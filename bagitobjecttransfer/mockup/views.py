from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

def index(request):
    return render(request, 'mockup/home.html')

def transfer(request):
    return render(request, 'mockup/transfer.html')

def sendtransfer(request):
    if request.method == 'POST':
        try:
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            print (f'First Name: {first_name} | Last Name: {last_name}')
        except KeyError:
            return render(request, 'mockup/transfer.html', {
                'error_msg': 'Transfer Failed, could not find first or last name in POST.'
            })
        else:
            return HttpResponseRedirect(reverse('mockup:transfersent'))
    else:
        return render(request, 'mockup/transfer.html')

def transfersent(request):
    return render(request, 'mockup/transfersent.html')
