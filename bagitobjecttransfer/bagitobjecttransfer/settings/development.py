# pylint: disable=wildcard-import
from pathlib import Path
from decouple import config
from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
]

# Sqlite database for development

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Local Redis Task Queue
# https://github.com/rq/django-rq

RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'PASSWORD': '',
        'DEFAULT_TIMEOUT': 360,
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

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
            'filename': Path(BASE_DIR).parent / 'redis' / 'rqworker.log',
            'formatter': 'standard',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO')
        },
        'recordtransfer': {
            'handlers': ['console'],
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
