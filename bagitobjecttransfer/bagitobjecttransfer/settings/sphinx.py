# Minimal settings for building docs with Sphinx
from .base import *

SITE_ID = 1

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

RQ_QUEUES = {
    'default': {
        'HOST': '0.0.0.0',
        'PORT': 6379,
        'DB': 0, # Redis database index
        'PASSWORD': '',
        'DEFAULT_TIMEOUT': 500,
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = '0.0.0.0'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False

SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

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
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}
