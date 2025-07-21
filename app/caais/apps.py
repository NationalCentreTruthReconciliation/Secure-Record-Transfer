import re

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


YYYY_MM_DD = re.compile(r'^[1-2]\d{3}-1[0-2]|0[1-9]-3[0-1]|[1-2][0-9]|0[1-9]$')


class CaaisConfig(AppConfig):
    ''' Application configuration for caais app
    '''

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'caais'

    # pylint: disable=consider-using-f-string
    def ready(self):
        try:
            if not YYYY_MM_DD.match(settings.CAAIS_UNKNOWN_START_DATE):
                raise ImproperlyConfigured((
                    'CAAIS_UNKNOWN_START_DATE "{}" does not conform to a '
                    'yyyy-mm-dd format (like 2000-01-01)'
                ).format(settings.CAAIS_UNKNOWN_START_DATE))
            if not YYYY_MM_DD.match(settings.CAAIS_UNKNOWN_END_DATE):
                raise ImproperlyConfigured((
                    'CAAIS_UNKNOWN_END_DATE "{}" does not conform to a '
                    'yyyy-mm-dd format (like 2010-12-31)'
                ).format(settings.CAAIS_UNKNOWN_START_DATE))
            if not settings.CAAIS_UNKNOWN_DATE_TEXT:
                raise ImproperlyConfigured(
                    'CAAIS_UNKNOWN_DATE_TEXT setting is empty'
                )

        except AttributeError as exc:
            match_obj = re.search(
                r'has no attribute ["\'](.+)["\']', str(exc), re.IGNORECASE
            )
            if match_obj:
                setting_name = match_obj.group(1)
                raise ImproperlyConfigured((
                    'The {0} setting is not defined in the Django settings!'
                ).format(setting_name)) from exc
            raise exc
