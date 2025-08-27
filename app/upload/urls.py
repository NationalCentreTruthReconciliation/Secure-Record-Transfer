from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = "upload"
urlpatterns = [
    path(
        "upload-session/",
        login_required(views.create_upload_session),
        name="create_upload_session",
    ),
    path(
        "upload-session/<session_token>/files/",
        login_required(views.upload_or_list_files),
        name="upload_files",
    ),
    path(
        "upload-session/<session_token>/files/<file_name>/",
        login_required(views.uploaded_file),
        name="uploaded_file",
    ),
]
