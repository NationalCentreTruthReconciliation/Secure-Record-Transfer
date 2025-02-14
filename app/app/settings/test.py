# Minimal settings for either testing, or building docs with Sphinx
import os
import tempfile
from pathlib import Path

from .base import *

DEBUG = True

TESTING = True

SITE_ID = 1

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        "TEST": {
            "NAME": os.path.join(BASE_DIR, "db.test.sqlite3"),
        },
    }
}

RQ_QUEUES = {
    "default": {
        "HOST": "0.0.0.0",
        "PORT": 6379,
        "DB": 0,  # Redis database index
        "PASSWORD": "",
        "DEFAULT_TIMEOUT": 500,
    },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "0.0.0.0"
EMAIL_PORT = 1025
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_USE_TLS = False

SILENCED_SYSTEM_CHECKS = ["django_recaptcha.recaptcha_test_key_error"]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

MIDDLEWARE_CLASSES = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{levelname} {asctime} {module}: {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "recordtransfer": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": True,
        },
        "rq.worker": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": True,
        },
        "clamav": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

BASE_DIR = tempfile.mkdtemp()
MEDIA_ROOT = str(Path(BASE_DIR) / "media")
TEMP_STORAGE_FOLDER = str(Path(MEDIA_ROOT) / "temp")
Path(TEMP_STORAGE_FOLDER).mkdir(parents=True, exist_ok=True)
UPLOAD_STORAGE_FOLDER = str(Path(MEDIA_ROOT) / "uploads")
Path(UPLOAD_STORAGE_FOLDER).mkdir(parents=True, exist_ok=True)
BAG_STORAGE_FOLDER = str(Path(MEDIA_ROOT) / "bags")

STATICFILES_DIRS = [
    os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ),
        "dist",
    ),
]
