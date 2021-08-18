recordtransfer.settings - Application Settings
==============================================

.. automodule:: recordtransfer.settings
   :members:

All options can be set by directly modifying the :code:`recordtransfer/settings.py` file or by
setting a value in the :code:`.env` environment file.


**BAG_STORAGE_FOLDER** *(string)*:
    The folder on the server where bags are to be stored.

    **This value can be set in the settings.py file or in the .env file**

    ::

        BAG_STORAGE_FOLDER=/path/to/your/folder


**APPROXIMATE_DATE_FORMAT** *(string)*:
    A format string for the date to indicate an approximate date. The string variable :code:`{date}`
    must be present for the date format to be used.

    **This value can be set in the settings.py file or in the .env file**

    ::

        APPROXIMATE_DATE_FORMAT='Circa. {date}'


**DO_NOT_REPLY_EMAIL** *(string)*:
    An email address for the application use to send emails from.

    **This value can be set in the settings.py file or in the .env file**

    ::

        DO_NOT_REPLY_EMAIL=donotreply@recordtransfer.ca


**ARCHIVIST_EMAIL** *(string)*:
    The email displayed for people to contact an archivist.

    **This value can be set in the settings.py file or in the .env file**

    ::

        ARCHIVIST_EMAIL=archives@domain.ca


**BASE_URL** *(string)*:
    The base URL of the website.

    **This value can be set in the settings.py file or in the .env file**

    ::

        BASE_URL=https://recordtransfer.ca


**ACCEPTED_FILE_FORMATS** *(dict)*:
    A dictionary of accepted file formats, each within a named group. You may name the groups
    anything you like. Make sure that file extensions do not start with a period, and that they
    are all lowercase. Group names should not be plural.

    The file extensions are used to determine what a user is allowed to upload. The group name is
    used to create a human-readable extent statement about the quantity and type of files the user
    uploaded.

    **This value can only be set in the settings.py file**

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


**DEFAULT_DATA** *(dict)*:
    Default data to inject into the form in case the user did not enter data in a field. These
    fields are important to fill out if the field is not in the form, and the field is mandatory in
    CAAIS.

    For example, there is no field for a 'repository' in the transfer form. Since it is mandatory in
    CAAIS, a default value must be placed in this dictionary under the 'section_1' key.

    On the other hand, if a field is not mandatory, the user does not need to enter anything. That
    being said, if you want a default value to be injected anyways, you can specify one here.

    It is not recommended to specify defaults for mandatory fields that the user is required to
    enter in the form since that may end up hiding possible exceptions that should be thrown for
    fields that are not filled out.

    Here is an example bare-bones configuration with the absolute minimum amount of fields set:

    **This value can only be set in the settings.py file**

    .. code-block:: python

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
                'event_agent': 'NCTR Digital Object Transfer Application',
            },
            'section_6': {
            },
            'section_7': {
                'rules_or_conventions': 'Canadian Archival Accession Information Standards v1.0',
                'action_type': 'Creation',
                'action_agent': 'Created with NCTR Record Transfer Portal',
                'language_of_accession_record': 'en',
            }
        }
