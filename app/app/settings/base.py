import os

from configuration import AcceptedFileTypes
from decouple import Csv, config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TESTING = False

SECRET_KEY = config("SECRET_KEY", default="q9n%k!e3k8vuoo9vnromslji*hsczyj84krzz1$g=i$wp2r!s-")

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

INSTALLED_APPS = [
    "caais.apps.CaaisConfig",
    "clamav.apps.ClamavConfig",
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
    "webpack_loader",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "app.urls"

loaders = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "recordtransfer.context_processors.signup_status",
                "recordtransfer.context_processors.file_upload_status",
                "recordtransfer.context_processors.constants_context",
            ],
            "loaders": loaders,
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
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
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

LANGUAGE_CODE = "en-us"

TIME_ZONE = config("TIME_ZONE", default="America/Winnipeg")

USE_I18N = True


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
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
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

# Email Usernames
DO_NOT_REPLY_USERNAME = config("DO_NOT_REPLY_USERNAME", default="do-not-reply")

ARCHIVIST_EMAIL = config("ARCHIVIST_EMAIL", default="archivist@example.com")

# Checksum types
BAG_CHECKSUMS = config("BAG_CHECKSUMS", default="sha512", cast=Csv())

# Maximum upload thresholds
MAX_TOTAL_UPLOAD_SIZE_MB = config("MAX_TOTAL_UPLOAD_SIZE_MB", default=256, cast=int)
MAX_SINGLE_UPLOAD_SIZE_MB = config("MAX_SINGLE_UPLOAD_SIZE_MB", default=64, cast=int)
MAX_TOTAL_UPLOAD_COUNT = config("MAX_TOTAL_UPLOAD_COUNT", default=40, cast=int)


# Pagination
PAGINATE_BY = config("PAGINATE_BY", default=10, cast=int)

# Use Date widgets for record dates or use free text fields.
USE_DATE_WIDGETS = config("USE_DATE_WIDGETS", default=True, cast=bool)

# Defaults to use in place of form data, or to supplement form data with when converted to CAAIS
# metadata
CAAIS_DEFAULT_REPOSITORY = config("CAAIS_DEFAULT_REPOSITORY", default="")
CAAIS_DEFAULT_ACCESSION_TITLE = config("CAAIS_DEFAULT_ACCESSION_TITLE", default="")
CAAIS_DEFAULT_ARCHIVAL_UNIT = config("CAAIS_DEFAULT_ARCHIVAL_UNIT", default="")
CAAIS_DEFAULT_DISPOSITION_AUTHORITY = config("CAAIS_DEFAULT_DISPOSITION_AUTHORITY", default="")
CAAIS_DEFAULT_ACQUISITION_METHOD = config("CAAIS_DEFAULT_ACQUISITION_METHOD", default="")
CAAIS_DEFAULT_STATUS = config("CAAIS_DEFAULT_STATUS", default="")
CAAIS_DEFAULT_SOURCE_CONFIDENTIALITY = config("CAAIS_DEFAULT_SOURCE_CONFIDENTIALITY", default="")
CAAIS_DEFAULT_PRELIMINARY_CUSTODIAL_HISTORY = config(
    "CAAIS_DEFAULT_PRELIMINARY_CUSTODIAL_HISTORY", default=""
)
CAAIS_DEFAULT_DATE_OF_MATERIALS = config("CAAIS_DEFAULT_DATE_OF_MATERIALS", default="")
CAAIS_DEFAULT_EXTENT_TYPE = config("CAAIS_DEFAULT_EXTENT_TYPE", default="")
CAAIS_DEFAULT_QUANTITY_AND_UNIT_OF_MEASURE = config(
    "CAAIS_DEFAULT_QUANTITY_AND_UNIT_OF_UNITS", default=""
)
CAAIS_DEFAULT_CONTENT_TYPE = config("CAAIS_DEFAULT_CONTENT_TYPE", default="")
CAAIS_DEFAULT_CARRIER_TYPE = config("CAAIS_DEFAULT_CARRIER_TYPE", default="")
CAAIS_DEFAULT_EXTENT_NOTE = config("CAAIS_DEFAULT_EXTENT_NOTE", default="")
CAAIS_DEFAULT_PRELIMINARY_SCOPE_AND_CONTENT = config(
    "CAAIS_DEFAULT_PRELIMINARY_SCOPE_AND_CONTENT", default=""
)
CAAIS_DEFAULT_LANGUAGE_OF_MATERIAL = config("CAAIS_DEFAULT_LANGUAGE_OF_MATERIAL", default="")
CAAIS_DEFAULT_STORAGE_LOCATION = config("CAAIS_DEFAULT_STORAGE_LOCATION", default="")
CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_TYPE = config(
    "CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_TYPE", default=""
)
CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_VALUE = config(
    "CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_VALUE", default=""
)
CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_NOTE = config(
    "CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_NOTE", default=""
)
CAAIS_DEFAULT_APPRAISAL_TYPE = config("CAAIS_DEFAULT_APPRAISAL_TYPE", default="")
CAAIS_DEFAULT_APPRAISAL_VALUE = config("CAAIS_DEFAULT_APPRAISAL_VALUE", default="")
CAAIS_DEFAULT_APPRAISAL_NOTE = config("CAAIS_DEFAULT_APPRAISAL_NOTE", default="")
CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TYPE = config(
    "CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TYPE", default=""
)
CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TITLE = config(
    "CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TITLE", default=""
)
CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_NOTE = config(
    "CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_NOTE", default=""
)
CAAIS_DEFAULT_GENERAL_NOTE = config("CAAIS_DEFAULT_GENERAL_NOTE", default="")
CAAIS_DEFAULT_RULES_OR_CONVENTIONS = config("CAAIS_DEFAULT_RULES_OR_CONVENTIONS", default="")
CAAIS_DEFAULT_LANGUAGE_OF_ACCESSION_RECORD = config(
    "CAAIS_DEFAULT_LANGUAGE_OF_ACCESSION_RECORD", default=""
)

# Special variables for default "Submission" type event when metadata is first created
CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE = config(
    "CAAIS_DEFAULT_EVENT_TYPE", default="Transfer Submitted"
)
CAAIS_DEFAULT_SUBMISSION_EVENT_AGENT = config("CAAIS_DEFAULT_EVENT_TYPE", default="")
CAAIS_DEFAULT_SUBMISSION_EVENT_NOTE = config("CAAIS_DEFAULT_EVENT_TYPE", default="")

# Special variables for default "Creation" type event when metadata is first created
CAAIS_DEFAULT_CREATION_TYPE = config("CAAIS_DEFAULT_CREATION_TYPE", default="Creation")
CAAIS_DEFAULT_CREATION_AGENT = config("CAAIS_DEFAULT_CREATION_AGENT", default="")
CAAIS_DEFAULT_CREATION_NOTE = config("CAAIS_DEFAULT_CREATION_NOTE", default="")

APPROXIMATE_DATE_FORMAT = config("APPROXIMATE_DATE_FORMAT", default="[ca. {date}]")

# File types allowed to be uploaded. See documentation for how to customize this list.
ACCEPTED_FILE_FORMATS = config(
    "ACCEPTED_FILE_TYPES",
    cast=AcceptedFileTypes(),
    default="Archive:zip|Audio:mp3,wav,flac|Document:docx,odt,pdf,txt,html|Image:jpg,jpeg,png,gif|Spreadsheet:xlsx,csv|Video:mkv,mp4",
)

# Media file storage locations
BAG_STORAGE_FOLDER = config("BAG_STORAGE_FOLDER", default=os.path.join(MEDIA_ROOT, "bags"))
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
