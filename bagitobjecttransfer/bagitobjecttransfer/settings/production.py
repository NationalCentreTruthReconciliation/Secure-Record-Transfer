# pylint: disable=wildcard-import
from decouple import config
from .base import *

# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/
DEBUG = False

ALLOWED_HOSTS = [
    # Add host domain(s) here
]


# MySQL database for production

DATABASES = {
    'default': {
        # Requires MySQL Connector/Python
        'ENGINE': 'mysql.connector.django',
        'OPTIONS': {
            # MySQL configuration files
            # https://dev.mysql.com/doc/refman/8.0/en/option-files.html
            'read_default_file': '/path/to/mysqld.cnf'
        },
    }
}


# Redis task queues
# https://github.com/rq/django-rq#deploying-on-ubuntu

RQ_QUEUES = {
    'default': {
        'HOST': config('RQ_HOST_DEFAULT'),
        'PORT': config('RQ_PORT_DEFAULT'),
        'DB': config('RQ_DB_DEFAULT'),
        'PASSWORD': config('RQ_PASSWORD_DEFAULT'),
        'DEFAULT_TIMEOUT': config('RQ_TIMEOUT_DEFAULT', default=360),
    },
}


# Emailing

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
EMAIL_USE_SSL = True


# Logging

LOGGING = {
#    'version': 1,
#    'disable_existing_loggers': False,
#    'formatters': {
#        'standard': {
#            'format': '{levelname} {asctime} {module}: {message}',
#            'style': '{'
#        }
#    },
#    'handlers': {
#        'console': {
#            'class': 'logging.StreamHandler',
#            'formatter': 'standard'
#        },
#    },
#    'loggers': {
#        'django': {
#            'handlers': ['console'],
#            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO')
#        },
#        'recordtransfer': {
#            'handlers': ['console'],
#            'level': 'INFO',
#            'propagate': True,
#        },
#        'rq.worker': {
#            'handlers': ['console'],
#            'level': 'INFO',
#            'propagate': True,
#        }
#    }
}
