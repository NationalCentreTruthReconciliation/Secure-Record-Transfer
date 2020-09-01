from django.urls import path
from django.forms import formset_factory
from django.contrib.auth.decorators import login_required

from . import views
from . import forms

app_name = 'recordtransfer'
urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('pretransfer/', login_required(views.FormPreparation.as_view()),
         name='formpreparation'),
    path('transfer/', login_required(views.TransferFormWizard.as_view([
        ('sourceinfo', forms.SourceInfoForm),
        ('contactinfo', forms.ContactInfoForm),
        ('recorddescription', forms.RecordDescriptionForm),
        ('rights', formset_factory(forms.RightsForm, extra=1)),
        ('otheridentifiers', formset_factory(forms.OtherIdentifiersForm, extra=1)),
        ('uploadfiles', forms.UploadFilesForm),
        ])), name='transfer'),
    path('transfer/uploadfile/', login_required(views.uploadfiles), name='uploadfile'),
    path('transfer/sent/', views.TransferSent.as_view(), name='transfersent'),
]
