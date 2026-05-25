from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.decorators.cache import never_cache

from . import views

app_name = "upload"
urlpatterns = [
    # Session-token-less endpoints. The upload session is resolved on the server from the opaque
    # per-wizard handle sent in the X-Upload-Handle request header.
    path(
        "upload-session/files/",
        never_cache(login_required(views.upload_or_list_files)),
        name="upload_files",
    ),
    path(
        "upload-session/files/<file_name>/",
        never_cache(login_required(views.uploaded_file_by_name)),
        name="uploaded_file_by_name",
    ),
    # Per-file access by opaque UUID. Used for browser-clickable file links (where custom request
    # headers aren't possible) so the upload session token does not need to be embedded in the URL.
    path(
        "uploaded-files/<uuid:file_uuid>/",
        login_required(views.uploaded_file_by_uuid),
        name="uploaded_file_by_uuid",
    ),
]
