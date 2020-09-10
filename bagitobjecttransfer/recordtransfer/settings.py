''' recordtransfer application specific settings '''
import platform

# The folder where bags will be stored
if platform.system() == 'Windows':
    BAG_STORAGE_FOLDER = 'C:/Users/dlove/Documents/NCTR/Bags'
else:
    BAG_STORAGE_FOLDER = '/mnt/c/Users/dlove/Documents/NCTR/Bags'


# The folder where reports will be output
if platform.system() == 'Windows':
    REPORT_FOLDER = 'C:/Users/dlove/Documents/NCTR/Bags/Reports'
else:
    REPORT_FOLDER = '/mnt/c/Users/dlove/Documents/NCTR/Bags/Reports'

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

ARCHIVIST_EMAILS = ['test@example.com']
