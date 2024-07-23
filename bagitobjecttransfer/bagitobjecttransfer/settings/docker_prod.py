# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from pathlib import Path
from decouple import config
from .base import *
import re

DEBUG = False
SITE_ID = config('SITE_ID', default=1, cast=int)

ALLOWED_HOSTS = re.split(r'\s+', config('ALLOWED_HOSTS'))

# MySQL Database

DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'HOST': config('MYSQL_HOST'),
        'PORT': config('MYSQL_PORT', cast=int, default=3306),
        'USER': config('MYSQL_USER'),
        'PASSWORD': config('MYSQL_PASSWORD'),
        'NAME': config('MYSQL_DATABASE'),
    }
}

# Asynchronous Redis Task Queue Manager
# https://github.com/rq/django-rq

RQ_QUEUES = {
    'default': {
        'HOST': config('REDIS_HOST', default='redis'),
        'PORT': config('REDIS_PORT', cast=int, default=6379),
        'DB': 0, # Redis database index
        'PASSWORD': config('REDIS_PASSWORD', default=''),
        'DEFAULT_TIMEOUT': 500,
    },
}

RQ_SHOW_ADMIN_LINK = True


# Emailing

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=25)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)


# Captcha

SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']


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
            'formatter': 'standard'
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

STATICFILES_STORAGE = 'pipeline.storage.PipelineManifestStorage'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)

# create separate minified stylesheets and javascript files for each app
PIPELINE = {
    'YUGLIFY_BINARY': os.path.join(BASE_DIR, 'node_modules/.bin/yuglify'),
    'STYLESHEETS': {
        'caais_styles': {
            'source_filenames': (
                'caais/css/*.css',
            ),
            'output_filename': 'caais/css/min.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
        'recordtransfer_styles': {
            'source_filenames': (
                'recordtransfer/css/*.css',
            ),
            'output_filename': 'recordtransfer/css/min.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
    },
    'JAVASCRIPT': {
        'caais_js': {
            'source_filenames': (
                'caais/js/*.js',
            ),
            'output_filename': 'caais.js',
        },
        'recordtransfer_base_js': {
            'source_filenames': (
                'recordtransfer/js/base/*.js',
            ),
            'output_filename': 'recordtransfer/js/base_min.js',
        },
        'recordtransfer_dropzone_js': {
            'source_filenames': (
                'recordtransfer/js/dropzone/*.js',
            ),
            'output_filename': 'recordtransfer/js/dropzone_min.js',
        },
    }
}

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MIDDLEWARE.extend([
    'django.middleware.gzip.GZipMiddleware',
    'pipeline.middleware.MinifyHTMLMiddleware',
])