# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from pathlib import Path
from decouple import config
from .base import *

DEBUG = True
SITE_ID = 1

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
]

# MySQL Database

DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'HOST': 'db',
        'PORT': 3306,
        'USER': config('MYSQL_USER'),
        'PASSWORD': config('MYSQL_PASSWORD'),
        'NAME': config('MYSQL_DATABASE'),
    }
}


# Asynchronous Redis Task Queue Manager
# https://github.com/rq/django-rq

RQ_QUEUES = {
    'default': {
        'HOST': 'redis',
        'PORT': 6379,
        'DB': 0, # Redis database index
        'PASSWORD': '',
        'DEFAULT_TIMEOUT': 500,
    },
}


# Emailing - Uses MailHog to intercept emails
# MailHog web UI runs at localhost:8025
# More information: https://github.com/mailhog/MailHog

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False


# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{levelname} {asctime} {module}: {message}',
            'style': '{'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'rqworker_file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/django-rq/rqworker.log',
            'formatter': 'standard',
        },
        'recordtransfer_file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/recordtransfer.log',
            'formatter': 'standard',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO')
        },
        'recordtransfer': {
            'handlers': ['recordtransfer_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'rq.worker': {
            'handlers': ['rqworker_file'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}
