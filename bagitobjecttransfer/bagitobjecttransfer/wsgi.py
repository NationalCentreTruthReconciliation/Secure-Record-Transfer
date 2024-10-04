"""
WSGI config for bagitobjecttransfer project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os
from decouple import config

from django.core.wsgi import get_wsgi_application

os.environ['DJANGO_SETTINGS_MODULE'] = config('DJANGO_SETTINGS_MODULE',
    default='bagitobjecttransfer.settings.docker_production')

application = get_wsgi_application()
