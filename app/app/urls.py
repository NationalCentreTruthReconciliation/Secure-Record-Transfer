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

from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from recordtransfer.views.account import AsyncPasswordResetView, Login

urlpatterns = [
    path("admin/django_rq/", include("django_rq.urls")),
    path("admin/", admin.site.urls),
    path("", include("recordtransfer.urls")),
    path(
        "account/password_reset/",
        AsyncPasswordResetView.as_view(),
    ),
    # Override the login view with redirect behavior
    path(
        "account/login/",
        Login.as_view(),
        name="login",
    ),
    path("account/", include("django.contrib.auth.urls")),
]

if settings.DEBUG:
    urlpatterns += debug_toolbar_urls()
