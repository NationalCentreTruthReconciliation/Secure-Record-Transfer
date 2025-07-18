"""CAAIS app settings."""

from django.conf import settings

# CAAIS update tracking settings
CAAIS_DEFAULT_UPDATE_TYPE = getattr(settings, "CAAIS_DEFAULT_UPDATE_TYPE", "Update")
CAAIS_DEFAULT_UPDATE_AGENT = getattr(settings, "CAAIS_DEFAULT_UPDATE_AGENT", "")
CAAIS_DEFAULT_UPDATE_NOTE = getattr(settings, "CAAIS_DEFAULT_UPDATE_NOTE", "")
