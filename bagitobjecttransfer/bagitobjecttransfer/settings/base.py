import os

from decouple import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TESTING = False

SECRET_KEY = config('SECRET_KEY', default='q9n%k!e3k8vuoo9vnromslji*hsczyj84krzz1$g=i$wp2r!s-')

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

INSTALLED_APPS = [
    'caais.apps.CaaisConfig',
    'clamav.apps.ClamavConfig',
    'recordtransfer.apps.RecordTransferConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_countries',
    'django.forms',
    'formtools',
    'django_rq',
    'django_recaptcha',
    'dbtemplates',
    'pipeline',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'pipeline.middleware.MinifyHTMLMiddleware',
]

ROOT_URLCONF = 'bagitobjecttransfer.urls'


# django-dbtemplates configuration
DBTEMPLATES_ENABLED = config('DBTEMPLATES_ENABLED', default=False, cast=bool)
DBTEMPLATES_USE_CODEMIRROR = True
DBTEMPLATES_AUTO_POPULATE_CONTENT = False


loaders = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
]

if DBTEMPLATES_ENABLED:
    loaders.append('dbtemplates.loader.Loader')


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'recordtransfer.context_processors.signup_status',
                'recordtransfer.context_processors.file_upload_status',
                'recordtransfer.context_processors.file_uploads',
            ],
            'loaders': loaders,
        },
    },
]

# Database primary key fields

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# WSGI

WSGI_APPLICATION = 'bagitobjecttransfer.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGIN_REDIRECT_URL = '/'

AUTH_USER_MODEL = 'recordtransfer.User'

FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = config('TIME_ZONE', default='America/Winnipeg')

USE_I18N = True


USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale')
]

# django-countries configuration
# https://github.com/SmileyChris/django-countries

COUNTRIES_FIRST = [
    'CA',
    'US',
]

COUNTRIES_FLAG_URL = 'flags/{code}.gif'

# Media and Static files (CSS, JavaScript, Images)

MEDIA_URL = '/media/'
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static/')
FILE_UPLOAD_PERMISSIONS = 0o644

# CAAIS dates

CAAIS_UNKNOWN_DATE_TEXT = config('CAAIS_UNKNOWN_DATE_TEXT', cast=str, default='Unknown date')
CAAIS_UNKNOWN_START_DATE = config('CAAIS_UNKNOWN_START_DATE', cast=str, default='1800-01-01')
CAAIS_UNKNOWN_END_DATE = config('CAAIS_UNKNOWN_END_DATE', cast=str, default='2020-01-01')


# ClamAV Setup

CLAMAV_ENABLED = config('CLAMAV_ENABLED', cast=bool, default=True)
CLAMAV_HOST = config('CLAMAV_HOST', default='clamav')
CLAMAV_PORT = config('CLAMAV_PORT', cast=int, default=3310)

# Pipeline configuration

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": 'pipeline.storage.PipelineManifestStorage',
    },
}

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)

# Set up yuglify binary location

_YUGLIFY_BINARY_NAME = "yuglify" if os.name != "nt" else "yuglify.exe"
_YUGLIFY_BINARY_DIR = os.path.join(os.path.dirname(BASE_DIR), "node_modules/yuglify/dist/")
YUGLIFY_BINARY = config("YUGLIFY_BINARY", os.path.join(_YUGLIFY_BINARY_DIR, _YUGLIFY_BINARY_NAME))


# create separate minified stylesheets and javascript files for each app
PIPELINE = {
    'YUGLIFY_BINARY': YUGLIFY_BINARY,
    'STYLESHEETS': {
        'caais_styles': {
            'source_filenames': (
                'caais/css/base/*.css',
            ),
            'output_filename': 'caais/css/base/min.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
        'recordtransfer_base_styles': {
            'source_filenames': (
                'recordtransfer/css/base/*.css',
            ),
            'output_filename': 'recordtransfer/css/base/min.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
        'recordtransfer_submission_detail_styles': {
            'source_filenames': (
                'recordtransfer/css/submission_detail/*.css',
            ),
            'output_filename': 'recordtransfer/css/submission_detail/min.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
    },
    'JAVASCRIPT': {
        'caais_admin_js': {
            'source_filenames': (
                'caais/js/admin/*.js',
            ),
            'output_filename': 'caais/js/admin/min.js',
        },
        'recordtransfer_base_js': {
            'source_filenames': (
                'recordtransfer/js/base/*.js',
            ),
            'output_filename': 'recordtransfer/js/base/min.js',
        },
        'recordtransfer_dropzone_js': {
            'source_filenames': (
                'recordtransfer/js/dropzone/*.js',
            ),
            'output_filename': 'recordtransfer/js/dropzone/min.js',
        },
        'recordtransfer_profile_js': {
            'source_filenames': (
                'recordtransfer/js/profile/*.js',
            ),
            'output_filename': 'recordtransfer/js/profile/min.js',
        },
        'recordtransfer_submission_group_js': {
            'source_filenames': (
                'recordtransfer/js/submission_group/*.js',
            ),
            'output_filename': 'recordtransfer/js/submission_group/min.js',
        },
        'recordtransfer_admin_js': {
            'source_filenames': (
                'recordtransfer/js/admin/*.js',
            ),
            'output_filename': 'recordtransfer/js/admin/min.js',
        },
    }
}
