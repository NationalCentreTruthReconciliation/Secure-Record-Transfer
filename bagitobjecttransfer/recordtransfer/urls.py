from django.urls import path

from . import views
from . import forms
from django.forms import formset_factory

app_name = 'recordtransfer'
urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('transfer/', views.TransferFormWizard.as_view([
            ('sourceinfo', forms.SourceInfoForm),
            ('contactinfo', forms.ContactInfoForm),
            ('recorddescription', forms.RecordDescriptionForm),
            ('rightsandotheridentifiers', formset_factory(forms.RightsForm, extra=2)),
            ('uploadfiles', forms.UploadFilesForm),
        ]
    ), name='transfer'),
    path('transfer/uploadfile/', views.uploadfiles, name='uploadfile'),
    path('transfer/sent/', views.TransferSent.as_view(), name='transfersent'),
]
