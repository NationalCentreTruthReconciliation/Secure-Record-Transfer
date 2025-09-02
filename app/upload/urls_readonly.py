from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

urlpatterns = [
    path(
        "upload-session/<session_token>/files/<file_name>/",
        login_required(views.readonly_uploaded_file),
        name="uploaded_file",
    ),
]
