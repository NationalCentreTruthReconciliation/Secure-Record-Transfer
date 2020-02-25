from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return render(request, 'mockup/home.html')

def transfer(request):
    return render(request, 'mockup/transfer.html')
