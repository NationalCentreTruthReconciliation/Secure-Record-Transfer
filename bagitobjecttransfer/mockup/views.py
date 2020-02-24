from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse('Hello World!')

def transfer(request):
    return HttpResponse('Transfer Form')
