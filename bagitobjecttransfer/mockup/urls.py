from django.urls import path

from . import views

app_name = 'mockup'
urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('transfer/', views.Transfer.as_view(), name='transfer'),
    path('transfer/send/', views.sendtransfer, name='sendtransfer'),
    path('transfer/uploadfile/', views.uploadfiles, name='uploadfile'),
    path('transfer/sent/', views.TransferSent.as_view(), name='transfersent'),
]
