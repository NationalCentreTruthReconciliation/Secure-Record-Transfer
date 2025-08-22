import os

from configuration import AcceptedFileTypes
from decouple import Csv, config
from django.utils.translation import gettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TESTING = False

SECRET_KEY = config("SECRET_KEY", default="q9n%k!e3k8vuoo9vnromslji*hsczyj84krzz1$g=i$wp2r!s-")

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

INSTALLED_APPS = [
    "axes",
    "webpack_loader",
    "nginx.apps.NginxConfig",
    "caais.apps.CaaisConfig",
    "upload.apps.UploadConfig",
    "recordtransfer.apps.RecordTransferConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_countries",
    "django.forms",
    "formtools",
    "django_rq",
    "django_recaptcha",
    "django_htmx",
    "widget_tweaks",
]

AUTHENTICATION_BACKENDS = [
    # AxesBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    "axes.backends.AxesBackend",
    # Django ModelBackend is the default authentication backend.
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "recordtransfer.middleware.SaveUserLanguageMiddleware",  # After LocaleMiddleware
    # AxesMiddleware should be the last middleware in the MIDDLEWARE list.
    "axes.middleware.AxesMiddleware",
]

# Axes configuration
AXES_ENABLED = config("AXES_ENABLED", default=True, cast=bool)
AXES_FAILURE_LIMIT = config("AXES_FAILURE_LIMIT", default=5, cast=int)
AXES_WARNING_THRESHOLD = config("AXES_WARNING_THRESHOLD", default=3, cast=int)
AXES_COOLOFF_TIME = config("AXES_COOL_OFF_TIME", default=0.5, cast=float)  # in hours
AXES_LOCKOUT_PARAMETERS = [["username", "user_agent"]]
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_CALLABLE = "recordtransfer.views.account.lockout"
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False

ROOT_URLCONF = "app.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "recordtransfer.context_processors.signup_status",
                "recordtransfer.context_processors.file_upload_status",
                "recordtransfer.context_processors.constants_context",
            ],
        },
    },
]

# Database primary key fields

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# WSGI

WSGI_APPLICATION = "app.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "recordtransfer.validators.LengthRangeValidator",
        "OPTIONS": {"min_length": 10, "max_length": 30},
    },
    {
        "NAME": "recordtransfer.validators.CharacterCategoriesValidator",
        "OPTIONS": {"required_categories": 3},
    },
    {
        "NAME": "recordtransfer.validators.PasswordHistoryValidator",
        "OPTIONS": {"history_depth": 5},
    },
    {
        "NAME": "recordtransfer.validators.ContainsUserNameValidator",
    },
]

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/account/login/"

AUTH_USER_MODEL = "recordtransfer.User"

FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en"

TIME_ZONE = config("TIME_ZONE", default="America/Winnipeg")

USE_I18N = True

LANGUAGES = [
    ("en", _("English")),
    ("fr", _("French")),
    ("hi", _("Hindi")),
]

LANGUAGE_COOKIE_NAME = "django_language"  # optional, included for clarity

USE_TZ = True

LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]

# django-countries configuration
# https://github.com/SmileyChris/django-countries

COUNTRIES_FIRST = [
    "CA",
    "US",
]

COUNTRIES_FLAG_URL = "flags/{code}.gif"

# Media and Static files (CSS, JavaScript, Images)

MEDIA_URL = "/media/"
STATIC_URL = "/static/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
FILE_UPLOAD_PERMISSIONS = 0o644

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# Tell Django where to find Webpack-built assets

STATICFILES_DIRS = [
    os.path.join(os.path.dirname(BASE_DIR), "dist"),
]

# Storage settings
# Default STORAGES from Django documentation
# See: https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-STORAGES
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# CAAIS dates

CAAIS_UNKNOWN_DATE_TEXT = config("CAAIS_UNKNOWN_DATE_TEXT", cast=str, default="Unknown date")
CAAIS_UNKNOWN_START_DATE = config("CAAIS_UNKNOWN_START_DATE", cast=str, default="1800-01-01")
CAAIS_UNKNOWN_END_DATE = config("CAAIS_UNKNOWN_END_DATE", cast=str, default="2020-01-01")


# ClamAV Setup

CLAMAV_ENABLED = config("CLAMAV_ENABLED", cast=bool, default=True)
CLAMAV_HOST = config("CLAMAV_HOST", default="clamav")
CLAMAV_PORT = config("CLAMAV_PORT", cast=int, default=3310)

# Enable or disable the sign-up ability
SIGN_UP_ENABLED = config("SIGN_UP_ENABLED", default=True, cast=bool)

# Enable or disable the file upload ability
FILE_UPLOAD_ENABLED = config("FILE_UPLOAD_ENABLED", default=True, cast=bool)

# Checksum types
BAG_CHECKSUMS = config("BAG_CHECKSUMS", default="sha512", cast=Csv())

# Maximum upload thresholds
MAX_TOTAL_UPLOAD_SIZE_MB = config("MAX_TOTAL_UPLOAD_SIZE_MB", default=256, cast=int)
MAX_SINGLE_UPLOAD_SIZE_MB = config("MAX_SINGLE_UPLOAD_SIZE_MB", default=64, cast=int)
MAX_TOTAL_UPLOAD_COUNT = config("MAX_TOTAL_UPLOAD_COUNT", default=40, cast=int)


# Use Date widgets for record dates or use free text fields.
USE_DATE_WIDGETS = config("USE_DATE_WIDGETS", default=True, cast=bool)

APPROXIMATE_DATE_FORMAT = config("APPROXIMATE_DATE_FORMAT", default="[ca. {date}]")

# File types allowed to be uploaded. See documentation for how to customize this list.
ACCEPTED_FILE_FORMATS = config(
    "ACCEPTED_FILE_TYPES",
    cast=AcceptedFileTypes(),
    default="Archive:zip|Audio:mp3,wav,flac|Document:docx,odt,pdf,txt,html|Image:jpg,jpeg,png,gif|Spreadsheet:xlsx,csv|Video:mkv,mp4",
)

# Media file storage locations
UPLOAD_STORAGE_FOLDER = config(
    "UPLOAD_STORAGE_FOLDER", default=os.path.join(MEDIA_ROOT, "uploaded_files")
)
TEMP_STORAGE_FOLDER = config("TEMP_STORAGE_FOLDER", default=os.path.join(MEDIA_ROOT, "temp"))

# Upload session settings
UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES = config(
    "UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", default=1440, cast=int
)

UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES = config(
    "UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", default=480, cast=int
)

UPLOAD_SESSION_EXPIRED_CLEANUP_SCHEDULE = config(
    "UPLOAD_SESSION_EXPIRED_CLEANUP_SCHEDULE",
    default="0 2 * * *",
    cast=str,
)

IN_PROGRESS_SUBMISSION_EXPIRING_EMAIL_SCHEDULE = config(
    "IN_PROGRESS_SUBMISSION_EXPIRING_EMAIL_SCHEDULE",
    default="0 * * * *",
    cast=str,
)

FIXTURE_DIRS = [
    os.path.join(BASE_DIR, "fixtures"),
]

SELENIUM_TESTS_HEADLESS_MODE = config("SELENIUM_TESTS_HEADLESS_MODE", default=False, cast=bool)

WEBPACK_LOADER = {
    "DEFAULT": {
        "STATS_FILE": os.path.join(os.path.dirname(BASE_DIR), "dist", "webpack-stats.json"),
    },
}
