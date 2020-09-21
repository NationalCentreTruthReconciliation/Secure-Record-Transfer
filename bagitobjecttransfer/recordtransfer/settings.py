''' Application-specific settings for the recordtransfer app '''
import platform

# The location where bags will be stored

if platform.system() == 'Windows':
    BAG_STORAGE_FOLDER = 'C:/Users/dlove/Documents/NCTR/Bags'
else:
    BAG_STORAGE_FOLDER = '/mnt/c/Users/dlove/Documents/NCTR/Bags'


# Default data to inject into metadata, after the user enters their own metadata

DEFAULT_DATA = {
    'section_1': {
        'repository': 'NCTR',
        'archival_unit': 'NCTR Archives',
        'acqusition_method': 'Digital Transfer',
    },
    'section_2': {
    },
    'section_3': {
        'extent_statement_type': 'Extent received',
        'quantity_and_type_of_units': 'N/A',
        'extent_statement_note': 'Files counted automatically by application',
    },
    'section_4': {
        'storage_location': 'N/A',
        'material_assessment_statement': 'N/A',
        'appraisal_statement': 'N/A',
        'associated_documentation': 'N/A',
    },
    'section_5': {
        'event_type': 'Digital Object Transfer',
        'event_agent': 'NCTR Digital Object Transfer Application',
    },
    'section_6': {
        'general_notes': 'N/A',
    },
    'section_7': {
        'rules_or_conventions': 'Canadian Archival Accession Information Standards v1.0',
        'action_type': 'Created',
        'action_agent': 'N/A',
        'action_note': 'Created with NCTR Record Transfer Portal',
    }
}


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
