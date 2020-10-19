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
        ('contactinfo', forms.ContactInfoForm),
        ('sourceinfo', forms.SourceInfoForm),
        ('recorddescription', forms.RecordDescriptionForm),
        ('rights', formset_factory(forms.RightsForm, extra=1)),
        ('otheridentifiers', formset_factory(forms.OtherIdentifiersForm, extra=1)),
        ('generalnotes', forms.GeneralNotesForm),
        ('uploadfiles', forms.UploadFilesForm),
        ])), name='transfer'),
    path('transfer/uploadfile/', login_required(views.uploadfiles), name='uploadfile'),
    path('transfer/sent/', views.TransferSent.as_view(), name='transfersent'),

    path('about/', views.About.as_view(), name='about'),
    path('profile/', login_required(views.UserProfile.as_view()), name='userprofile'),
]
