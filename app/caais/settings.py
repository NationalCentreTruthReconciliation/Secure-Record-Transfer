"""CAAIS app settings."""

from django.conf import settings

CAAIS_DEFAULT_UPDATE_TYPE = getattr(settings, "CAAIS_DEFAULT_UPDATE_TYPE", "Update")
