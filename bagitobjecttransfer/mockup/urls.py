from django.urls import path

from . import views

app_name = 'mockup'
urlpatterns = [
    path('', views.index, name='index'),
    path('transfer/', views.transfer, name='transfer'),
    path('transfer/send/', views.sendtransfer, name='sendtransfer'),
    path('transfer/sent/', views.transfersent, name='transfersent'),
]
