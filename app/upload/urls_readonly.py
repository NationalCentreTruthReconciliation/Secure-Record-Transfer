from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

urlpatterns = [
    path(
        "uploaded-files/<uuid:file_uuid>/",
        login_required(views.uploaded_file_by_uuid),
        name="uploaded_file_by_uuid",
    ),
]
