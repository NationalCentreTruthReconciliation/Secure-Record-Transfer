from decouple import config
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    'captcha',
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

TIME_ZONE = 'America/Winnipeg'

USE_I18N = True

USE_L10N = True

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
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
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

