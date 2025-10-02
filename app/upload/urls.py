from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.decorators.cache import never_cache

from . import views

app_name = "upload"
urlpatterns = [
    path(
        "upload-session/<session_token>/files/",
        never_cache(login_required(views.upload_or_list_files)),
        name="upload_files",
    ),
    path(
        "upload-session/<session_token>/files/<file_name>/",
        never_cache(login_required(views.uploaded_file)),
        name="uploaded_file",
    ),
]
