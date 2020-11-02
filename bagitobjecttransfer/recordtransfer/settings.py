''' Application-specific settings for the recordtransfer app '''
import platform
from decouple import config

# The location where bags will be stored

if platform.system() == 'Windows':
    BAG_STORAGE_FOLDER = config('BAG_FOLDER_WINDOWS')
else:
    BAG_STORAGE_FOLDER = config('BAG_FOLDER_LINUX')

# Email address for automated emails

DO_NOT_REPLY_EMAIL = 'do-not-reply@nctrrecordtransfer.ca'

BASE_URL = 'http://127.0.0.1:8000'

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
        'storage_location': 'N/A',
        'appraisal_statement': 'N/A',
        'associated_documentation': 'N/A',
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


APPROXIMATE_DATE_FORMAT = '[ca. {date}]'

# File types allowed to be uploaded to the backend. Do not use periods before the extension, and
# ensure that all file extensions are lowercase.

ACCEPTED_FILE_FORMATS = {
    'Archive': [
        'zip',
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
    'Image': [
        'jpg',
        'jpeg',
        'gif',
        'png',
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
    'Audio': [
        'acc',
        'flac',
        'm4a',
        'mp3',
        'ogg',
        'wav',
        'wma',
    ],
}
