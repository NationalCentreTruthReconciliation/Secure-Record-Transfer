# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
import os

from decouple import config

from .base import *

DEBUG = True

INSTALLED_APPS += [
    "debug_toolbar",
]

# Insert debug toolbar middleware after GZipMiddleware
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.gzip.GZipMiddleware") + 1,
    "debug_toolbar.middleware.DebugToolbarMiddleware",
)

SITE_ID = config("SITE_ID", default=1, cast=int)

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
}

# MySQL Database

DEV_DATABASE_NAME = config("DEV_DATABASE_NAME", default="development_database.sqlite3")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, str(DEV_DATABASE_NAME)),
    }
}


# Asynchronous Redis Task Queue Manager
# https://github.com/rq/django-rq

RQ_QUEUES = {
    "default": {
        "HOST": config("REDIS_HOST", default="redis"),
        "PORT": config("REDIS_PORT", cast=int, default=6379),
        "DB": 0,  # Redis database index
        "PASSWORD": config("REDIS_PASSWORD", ""),
        "DEFAULT_TIMEOUT": 500,
    },
}

RQ_SHOW_ADMIN_LINK = True


# Emailing - Uses Mailpit to intercept emails
# Mailpit web UI runs at localhost:8025
# More information: https://github.com/axllent/mailpit

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "email"
EMAIL_PORT = 1025
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_USE_TLS = False


# Captcha

SILENCED_SYSTEM_CHECKS = ["django_recaptcha.recaptcha_test_key_error"]


# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "{levelname} {asctime} {module}: {message}", "style": "{"}
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": os.getenv("DJANGO_LOG_LEVEL", "INFO")},
        "recordtransfer": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "rq.worker": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "rq_scheduler": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "rq_scheduler.scheduler": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
