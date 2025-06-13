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

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from recordtransfer.views.account import AsyncPasswordResetView

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
        auth_views.LoginView.as_view(
            redirect_authenticated_user=True
        ),
        name="login",
    ),
    path("account/", include("django.contrib.auth.urls")),
]
