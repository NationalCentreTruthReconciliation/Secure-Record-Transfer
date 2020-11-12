# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from pathlib import Path
from decouple import config
from .base import *

DEBUG = True

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


# Local Redis Task Queue
# https://github.com/rq/django-rq

RQ_QUEUES = {
    'default': {
        'HOST': 'redis',
        'PORT': 6379,
        'DB': 0,
        'PASSWORD': '',
        'DEFAULT_TIMEOUT': 360,
    },
}


# Emailing

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False


# Logging

log_folder = Path(BASE_DIR) / 'logs'
REDIS_LOG_FILE = log_folder / 'redis-server.log'
RQ_WORKER_LOG_FILE = log_folder / 'rqworker.log'
MY_SQL_ERROR_LOG_FILE = log_folder / 'mysql_error.log'
MY_SQL_GENERAL_LOG_FILE = log_folder / 'mysql.log'
MY_SQL_SLOW_QUERY_LOG_FILE = log_folder / 'mysql_slow_queries.log'

for log_file in (
    REDIS_LOG_FILE,
    RQ_WORKER_LOG_FILE,
    MY_SQL_ERROR_LOG_FILE,
    MY_SQL_GENERAL_LOG_FILE,
    MY_SQL_SLOW_QUERY_LOG_FILE):
    if not log_file.exists():
        log_file.touch()

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
