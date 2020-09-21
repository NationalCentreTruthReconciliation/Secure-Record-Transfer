Application Settings (settings.py)
==================================

.. automodule:: recordtransfer.settings
   :members:


**ACCEPTED_FILE_FORMATS** *(dict)*:
    A dictionary of accepted file formats, each within a named group. You may name the groups
    anything you like. Make sure that file extensions do not start with a period, and that they
    are all lowercase. Group names should not be plural.

    The file extensions are used to determine what a user is allowed to upload. The group name is
    used to create a human-readable extent statement about the quantity and type of files the user
    uploaded.

.. code-block:: python

    # There is no limit to the number of groups or the number of extensions in a group.
    ACCEPTED_FILE_FORMATS = {
        'Archive': [
            'zip',
            '7z',
            'rar',
        ],
        'Document': [
            'doc',
            'docx',
        ],
        'Database': [
            'db',
            'sqlite3',
        ]
        'Photo': [
            'jpg',
            'jpeg',
            'png',
        ],
    }


**BAG_STORAGE_FOLDER** *(string)*:
    The folder on the server where bags are to be stored.

.. code-block:: python

    BAG_STORAGE_FOLDER = '/path/to/your/folder'


**DEFAULT_DATA** *(dict)*:
    Default data to inject into form data, after the user enters their own metadata. The following
    are all of the used keys:

.. code-block:: python

    DEFAULT_DATA = {
        'section_1': {
            'repository': 'The repository',
            'archival_unit': 'Archival unit name',
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
            'event_agent': 'Digital Object Transfer Application',
        },
        'section_6': {
            'general_notes': 'N/A',
        },
        'section_7': {
            'rules_or_conventions': 'Canadian Archival Accession Information Standards v1.0',
            'action_type': 'Created',
            'action_agent': 'N/A',
            'action_note': 'Created with Record Transfer Portal',
        }
    }
