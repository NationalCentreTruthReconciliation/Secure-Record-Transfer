''' Application-specific settings for the recordtransfer app '''
from decouple import config

# Enable or disable the sign-up ability

SIGN_UP_ENABLED = config('SIGN_UP_ENABLED', default=True, cast=bool)

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

# CLAMAV configuration.

CLAMD_HOST = config('CLAMD_HOST', default=None)
CLAMD_PORT = config('CLAMD_PORT', default=3310, cast=int)

# Default data to inject into metadata, after the user enters their own metadata

DEFAULT_DATA = {
    'section_1': {
        'accession_identifier': 'Not assigned',
        'repository': 'NCTR',
        'archival_unit': 'NCTR Archives',
        'acquisition_method': 'Digital Transfer',
    },
    'section_2': {
    },
    'section_3': {
        'extent_statement_type': 'Extent received',
        'extent_statement_note': 'Files counted automatically by application',
    },
    'section_4': {
        'storage_location': 'Placeholder',
        'material_assessment_statement_type': 'Physical Condition',
        'material_assessment_statement_value': 'Record is digital, physical assessment is not possible'
    },
    'section_5': {
        'event_type': 'Digital Object Transfer',
        'event_agent': 'NCTR Record Transfer Portal',
    },
    'section_6': {
    },
    'section_7': {
        'rules_or_conventions': 'Canadian Archival Accession Information Standards v1.0',
        'action_type': 'Creation',
        'action_agent': 'NCTR Record Transfer Portal',
        'language_of_accession_record': 'en',
    }
}


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
