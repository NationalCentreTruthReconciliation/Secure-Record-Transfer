# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from decouple import config

from .base import *

DEBUG = False
SITE_ID = config("SITE_ID", default=1, cast=int)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=str).split(",")
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=str).split(",")

SECRET_KEY = config("SECRET_KEY")

# MySQL Database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": config("MYSQL_HOST"),
        "PORT": config("MYSQL_PORT", cast=int, default=3306),
        "USER": config("MYSQL_USER"),
        "PASSWORD": config("MYSQL_PASSWORD"),
        "NAME": config("MYSQL_DATABASE"),
    }
}

# Asynchronous Redis Task Queue Manager
# https://github.com/rq/django-rq

RQ_QUEUES = {
    "default": {
        "HOST": config("REDIS_HOST", default="redis"),
        "PORT": config("REDIS_PORT", cast=int, default=6379),
        "DB": 0,  # Redis database index
        "PASSWORD": config("REDIS_PASSWORD", default=""),
        "DEFAULT_TIMEOUT": 500,
    },
}

RQ_SHOW_ADMIN_LINK = True


# Emailing

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", cast=int, default=25)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=False, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)


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
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
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
        "clamav": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

# Storage settings
# Hash static files for cache busting
STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
}
