from django.urls import path

from . import views
from . import forms

app_name = 'mockup'
urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('transfer/', views.TransferFormWizard.as_view([
        ('sourceinfo', forms.SourceInfoForm),
        ('contactinfo', forms.ContactInfoForm),
        ('recorddescription', forms.RecordDescriptionForm),
        ('uploadfiles', forms.UploadFilesForm),
    ]), name='transfer'),
    path('transfer/uploadfile/', views.uploadfiles, name='uploadfile'),
    path('transfer/sent/', views.TransferSent.as_view(), name='transfersent'),
]
