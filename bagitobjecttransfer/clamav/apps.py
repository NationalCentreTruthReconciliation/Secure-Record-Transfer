from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def verify_clamav_settings():
    ''' Verifies the settings exist and are properly configured:

    - CLAMAV_ENABLED
    - CLAMAV_HOST
    - CLAMAV_PORT
    '''
    enabled = settings.CLAMAV_ENABLED
    if enabled:
        if not settings.CLAMAV_HOST:
            raise ImproperlyConfigured('CLAMAV_HOST must be set in CLAMAV_ENABLED is True')
        if settings.CLAMAV_PORT <= 0:
            raise ImproperlyConfigured(f'CLAMAV_PORT value {settings.CLAMAV_PORT} is not valid (must be greater than zero)')


class ClamavConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clamav'

    def ready(self):
        try:
            verify_clamav_settings()

        except AttributeError as exc:
            raise ImproperlyConfigured(
                f'The "{exc.name}" setting is not defined! Ensure it exists in Django\'s configuration'
            ) from exc
