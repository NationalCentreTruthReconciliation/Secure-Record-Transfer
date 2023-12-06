from django.conf import settings

CLAMAV_ENABLED = getattr(settings, 'CLAMAV_ENABLED', True)
CLAMAV_HOST = getattr(settings, 'CLAMAV_HOST', 'clamav')
CLAMAV_PORT = getattr(settings, 'CLAMAV_PORT', 3310)
