''' Application-specific settings for the recordtransfer app '''
from decouple import config

# Enable or disable the sign-up ability

SIGN_UP_ENABLED = config('SIGN_UP_ENABLED', default=True, cast=bool)

# Enable or disable the file upload ability

FILE_UPLOAD_ENABLED = config('FILE_UPLOAD_ENABLED', default=True, cast=bool)

# The location where bags will be stored

BAG_STORAGE_FOLDER = config('BAG_STORAGE_FOLDER')

# The location where uploaded files are stored temporarily

UPLOAD_STORAGE_FOLDER = config('UPLOAD_STORAGE_FOLDER')

# Whether to allow updating BagIt bags

ALLOW_BAG_CHANGES = config('ALLOW_BAG_CHANGES', default=True, cast=bool)

# Email Usernames

DO_NOT_REPLY_USERNAME = config('DO_NOT_REPLY_USERNAME', default='do-not-reply')
ARCHIVIST_EMAIL = config('ARCHIVIST_EMAIL')

# Checksum types

BAG_CHECKSUMS = [
    algorithm.strip() for algorithm in config('BAG_CHECKSUMS', default='sha512').split(',')
]

# Maximum upload thresholds

MAX_TOTAL_UPLOAD_SIZE = config('MAX_TOTAL_UPLOAD_SIZE', default=256, cast=int)
MAX_SINGLE_UPLOAD_SIZE = config('MAX_SINGLE_UPLOAD_SIZE', default=64, cast=int)
MAX_TOTAL_UPLOAD_COUNT = config('MAX_TOTAL_UPLOAD_COUNT', default=40, cast=int)

# Use Date widgets for record dates or use free text fields.

USE_DATE_WIDGETS = config('USE_DATE_WIDGETS', default=True, cast=bool)

# Maximum number of saved transfers per user.

MAX_SAVED_TRANSFER_COUNT = config('MAX_SAVED_TRANSFER_COUNT', default=2, cast=int)

# Defaults to use in place of form data, or to supplement form data with when converted to CAAIS
# metadata

CAAIS_DEFAULT_REPOSITORY = config('CAAIS_DEFAULT_REPOSITORY', default='')
CAAIS_DEFAULT_ACCESSION_TITLE = config('CAAIS_DEFAULT_ACCESSION_TITLE', default='')
CAAIS_DEFAULT_ARCHIVAL_UNIT = config('CAAIS_DEFAULT_ARCHIVAL_UNIT', default='')
CAAIS_DEFAULT_ACQUISITION_METHOD = config('CAAIS_DEFAULT_ACQUISITION_METHOD', default='')
CAAIS_DEFAULT_DISPOSITION_AUTHORITY = config('CAAIS_DEFAULT_DISPOSITION_AUTHORITY', default='')
CAAIS_DEFAULT_STATUS = config('CAAIS_DEFAULT_STATUS', default='')
CAAIS_DEFAULT_SOURCE_CONFIDENTIALITY = config('CAAIS_DEFAULT_SOURCE_CONFIDENTIALITY', default='')
CAAIS_DEFAULT_PRELIMINARY_CUSTODIAL_HISTORY = config('CAAIS_DEFAULT_PRELIMINARY_CUSTODIAL_HISTORY', default='')
CAAIS_DEFAULT_DATE_OF_MATERIALS = config('CAAIS_DEFAULT_DATE_OF_MATERIALS', default='')
CAAIS_DEFAULT_EXTENT_TYPE = config('CAAIS_DEFAULT_EXTENT_TYPE', default='')
CAAIS_DEFAULT_QUANTITY_AND_UNIT_OF_MEASURE = config('CAAIS_DEFAULT_QUANTITY_AND_UNIT_OF_UNITS', default='')
CAAIS_DEFAULT_CONTENT_TYPE = config('CAAIS_DEFAULT_CONTENT_TYPE', default='')
CAAIS_DEFAULT_CARRIER_TYPE = config('CAAIS_DEFAULT_CARRIER_TYPE', default='')
CAAIS_DEFAULT_EXTENT_NOTE = config('CAAIS_DEFAULT_EXTENT_NOTE', default='')
CAAIS_DEFAULT_PRELIMINARY_SCOPE_AND_CONTENT = config('CAAIS_DEFAULT_PRELIMINARY_SCOPE_AND_CONTENT', default='')
CAAIS_DEFAULT_LANGUAGE_OF_MATERIAL = config('CAAIS_DEFAULT_LANGUAGE_OF_MATERIAL', default='')
CAAIS_DEFAULT_STORAGE_LOCATION = config('CAAIS_DEFAULT_STORAGE_LOCATION', default='')
CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_TYPE = config('CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_TYPE', default='')
CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_VALUE = config('CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_VALUE', default='')
CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_NOTE = config('CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_NOTE', default='')
CAAIS_DEFAULT_APPRAISAL_TYPE = config('CAAIS_DEFAULT_APPRAISAL_TYPE', default='')
CAAIS_DEFAULT_APPRAISAL_VALUE = config('CAAIS_DEFAULT_APPRAISAL_VALUE', default='')
CAAIS_DEFAULT_APPRAISAL_NOTE = config('CAAIS_DEFAULT_APPRAISAL_NOTE', default='')
CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TYPE = config('CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TYPE', default='')
CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TITLE = config('CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TITLE', default='')
CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_NOTE = config('CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_NOTE', default='')
CAAIS_DEFAULT_GENERAL_NOTE = config('CAAIS_DEFAULT_GENERAL_NOTE', default='')
CAAIS_DEFAULT_RULES_OR_CONVENTIONS = config('CAAIS_DEFAULT_RULES_OR_CONVENTIONS', default='')
CAAIS_DEFAULT_LANGUAGE_OF_ACCESSION_RECORD = config('CAAIS_DEFAULT_LANGUAGE_OF_ACCESSION_RECORD', default='')

# Special variables for default "Submission" type event when metadata is first created
CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE = config('CAAIS_DEFAULT_EVENT_TYPE', default='Transfer Submitted')
CAAIS_DEFAULT_SUBMISSION_EVENT_AGENT = config('CAAIS_DEFAULT_EVENT_TYPE', default='')
CAAIS_DEFAULT_SUBMISSION_EVENT_NOTE = config('CAAIS_DEFAULT_EVENT_TYPE', default='')

# Special variables for default "Creation" type event when metadata is first created
CAAIS_DEFAULT_CREATION_TYPE = config('CAAIS_DEFAULT_CREATION_TYPE', default='Creation')
CAAIS_DEFAULT_CREATION_AGENT = config('CAAIS_DEFAULT_CREATION_AGENT', default='')
CAAIS_DEFAULT_CREATION_NOTE = config('CAAIS_DEFAULT_CREATION_NOTE', default='')


APPROXIMATE_DATE_FORMAT = config('APPROXIMATE_DATE_FORMAT', default='[ca. {date}]')

# File types allowed to be uploaded to the backend. Do not use periods before the extension, and
# ensure that all file extensions are lowercase.

ACCEPTED_FILE_FORMATS = {
    'Archive': [
        'zip',
    ],
    'Audio': [
        'acc',
        'flac',
        'm4a',
        'mp3',
        'ogg',
        'wav',
        'wma',
    ],
    'Document': [
        'doc',
        'docx',
        'odt',
        'pdf',
        'rtf',
        'txt',
        'html',
    ],
    'Image': [
        'jpg',
        'jpeg',
        'gif',
        'png',
    ],
    'Presentation': [
        'ppt',
        'pptx',
        'pps',
        'ppsx',
    ],
    'Spreadsheet': [
        'xls',
        'xlsx',
        'csv',
    ],
    'Video': [
        'avi',
        'mkv',
        'mov',
        'mp4',
        'mpeg4',
        'mpg',
        'wmv',
    ],
}
