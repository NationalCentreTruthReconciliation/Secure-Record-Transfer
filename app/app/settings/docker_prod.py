from decouple import config

from .base import *

DEBUG = False
SITE_ID = config("SITE_ID", default=1, cast=int)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=str).split(",")
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=str).split(",")

SECRET_KEY = config("SECRET_KEY", cast=str)

# Extra Middleware for caching

_axes_middleware_index = 0

try:
    _axes_middleware_index = MIDDLEWARE.index("axes.middleware.AxesMiddleware")
except ValueError:
    # Set it to the end by default
    _axes_middleware_index = len(MIDDLEWARE) - 1

# Insert FetchFromCache at the end (before the Axes middleware) and insert UpdateCache at the start
MIDDLEWARE.insert(_axes_middleware_index - 1, "django.middleware.cache.FetchFromCacheMiddleware")
MIDDLEWARE.insert(0, "django.middleware.cache.UpdateCacheMiddleware")


# Recaptcha
RECAPTCHA_PUBLIC_KEY = config("RECAPTCHA_PUBLIC_KEY", cast=str, default="")
RECAPTCHA_PRIVATE_KEY = config("RECAPTCHA_PRIVATE_KEY", cast=str, default="")


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


# Cache setup (shares Redis with the task queue)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{config('REDIS_HOST', default='redis')}:{config('REDIS_PORT', cast=int, default=6379)}",
    }
}

CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = config("CACHE_MIDDLEWARE_SECONDS", cast=int, default=86400)
CACHE_MIDDLEWARE_KEY_PREFIX = config(
    "CACHE_MIDDLEWARE_KEY_PREFIX", default="secure-record-transfer-01"
)


# Emailing

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", cast=int, default=25)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=False, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)


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
