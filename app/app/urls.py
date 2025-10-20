"""app URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.cache import cache_page
from django.views.i18n import JavaScriptCatalog
from nginx.errors import custom_404
from recordtransfer.views.account import (
    AsyncPasswordChangeView,
    AsyncPasswordResetConfirmView,
    AsyncPasswordResetView,
    Login,
)
from utility import get_js_translation_version

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("admin/django_rq/", include("django_rq.urls")),
    path("admin/", admin.site.urls),
    path("", include("recordtransfer.urls")),
    # Custom auth views - these override Django's built-in views
    path(
        "account/login/",
        Login.as_view(),
        name="login",
    ),
    path(
        "account/password_change/",
        AsyncPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "account/password_reset/",
        AsyncPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "account/reset/<uidb64>/<token>/",
        AsyncPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # Django's built-in auth URLs (remaining views that aren't overridden)
    path("account/", include("django.contrib.auth.urls")),
    path(
        "jsi18n/",
        cache_page(86400, key_prefix="jsi18n-%s" % get_js_translation_version())(
            JavaScriptCatalog.as_view()
        ),
        name="javascript-catalog",
    ),
    path("404/", custom_404, name="404-not-found"),
]

if settings.DEBUG:
    # Serve media files directly without nginx in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG and not settings.TESTING:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()

if settings.TESTING or settings.FILE_UPLOAD_ENABLED:
    urlpatterns += [path("", include("upload.urls"))]
elif not settings.FILE_UPLOAD_ENABLED:
    urlpatterns += [path("", include("upload.urls_readonly"))]
