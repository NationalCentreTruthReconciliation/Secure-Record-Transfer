recordtransfer.settings - Application Settings
==============================================

.. automodule:: recordtransfer.settings
   :members:

These settings control the behaviour of the application. All options can be set by directly
modifying the :code:`recordtransfer/settings.py` file, and some may be changed by setting a value in
the :code:`.env` environment file. These settings are organized by category below.

.. contents:: List of Settings


Application Features
--------------------


MAX_SAVED_TRANSFER_COUNT
^^^^^^^^^^^^^^^^^^^^^^^^

    *Choose maximum saved transfers per user*

    .. table::

        ========  ======================  =========  ==================  =========================
        Required  Default                 Type       Can be set in .env  Can be set in settings.py
        ========  ======================  =========  ==================  =========================
        NO        2                       int        YES                 YES
        ========  ======================  =========  ==================  =========================

    The maximum number of transfers a user can save to resume later. Must be a non-negative integer.
    Set to 0 to disable saving transfers.

    **.env Example:**

    ::

        #file: .env
        MAX_SAVED_TRANSFER_COUNT=5


SIGN_UP_ENABLED
^^^^^^^^^^^^^^^

    *Choose whether new users can sign up*

    .. table::

        ========  ============  =========  ==================  =========================
        Required  Default       Type       Can be set in .env  Can be set in settings.py
        ========  ============  =========  ==================  =========================
        NO        True          bool       YES                 YES
        ========  ============  =========  ==================  =========================

    You may want to create users manually to tightly control who has access to the application. In
    this case, you will want to disable signing up so that no new users can be created without an
    admin creating them.

    **.env Example:**

    ::

        #file: .env
        SIGN_UP_ENABLED=false


FILE_UPLOAD_ENABLED
^^^^^^^^^^^^^^^^^^^

    *Choose whether to allow file uploads*

    .. table::

        ========  ============  =========  ==================  =========================
        Required  Default       Type       Can be set in .env  Can be set in settings.py
        ========  ============  =========  ==================  =========================
        NO        True          bool       YES                 YES
        ========  ============  =========  ==================  =========================

    Sets whether file uploads are allowed. If they are *not* allowed (disabled), then only metadata
    is submitted to the application.

    **.env Example:**

    ::

        #file: .env
        FILE_UPLOAD_ENABLED=false


USE_DATE_WIDGETS
^^^^^^^^^^^^^^^^

  *Use javascript date widgets*

  .. table::

      ========  ============  =========  ==================  =========================
      Required  Default       Type       Can be set in .env  Can be set in settings.py
      ========  ============  =========  ==================  =========================
      NO        True          bool       YES                 YES
      ========  ============  =========  ==================  =========================

  By default you must enter full dates in the format YYYY-MM-DD for records start and end dates.
  Setting this to False allows users to enter free text for the start and end date fields.

  **.env Example:**

  ::

      #file: .env
      USE_DATE_WIDGETS=false


DBTEMPLATES_ENABLED
^^^^^^^^^^^^^^^^^^^

  *Enable or disable changing templates from Django admin*

  .. table::

      ========  ============  =========  ==================  =========================
      Required  Default       Type       Can be set in .env  Can be set in settings.py
      ========  ============  =========  ==================  =========================
      NO        False         bool       YES                 NO
      ========  ============  =========  ==================  =========================

  It is possible to enable this setting so that site templates can be changed without having to
  re-deploy the application. Be careful with enabling this - it is very easy to break templates,
  hence why it is **disabled** by default.

  **.env Example:**

  ::

      #file: .env
      DBTEMPLATES_ENABLED=false


CLAMAV_ENABLED
^^^^^^^^^^^^^^

    *Whether ClamAV checking is enabled*

    .. table::

        ========  ===============  =========  ==================  =========================
        Required  Default          Type       Can be set in .env  Can be set in settings.py
        ========  ===============  =========  ==================  =========================
        YES       True             bool       YES                 YES
        ========  ===============  =========  ==================  =========================

    Enables/disables whether ClamAV malware checking is enabled.

    If the :ref:`FILE_UPLOAD_ENABLED` setting is disabled, this option has no effect.

    **.env Example:**

    ::

        #file: .env
        CLAMAV_ENABLED=True


File Upload Controls
--------------------

These settings have no effect if :ref:`FILE_UPLOAD_ENABLED` is False.


ACCEPTED_FILE_FORMATS
^^^^^^^^^^^^^^^^^^^^^

    *Choose what files (by extension) can be uploaded*

    .. table::

        ========  ===============  =========  ==================  =========================
        Required  Default          Type       Can be set in .env  Can be set in settings.py
        ========  ===============  =========  ==================  =========================
        NO        See settings.py  dict       NO                  YES
        ========  ===============  =========  ==================  =========================

    .. seealso::

        See also the section of the docs on :ref:`Accepted File Types`.

    A dictionary of accepted file formats, each within a named group. You may name the groups
    anything you like. Make sure that file extensions do not start with a period, and that they
    are all lowercase. Group names should not be plural.

    The file extensions are used to determine what a user is allowed to upload. The group name is
    used to create a human-readable extent statement about the quantity and type of files the user
    uploaded.

    If the :ref:`FILE_UPLOAD_ENABLED` setting is disabled, this option has no effect.

    **settings.py Example:**

    .. code-block:: python

        #file: settings.py
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


MAX_SINGLE_UPLOAD_SIZE
^^^^^^^^^^^^^^^^^^^^^^

    *Choose the maximum size (in MiB) an uploaded file is allowed to be*

    .. table::

        ========  ============  =========  ==================  =========================
        Required  Default       Type       Can be set in .env  Can be set in settings.py
        ========  ============  =========  ==================  =========================
        NO        64            int        YES                 YES
        ========  ============  =========  ==================  =========================

    Sets the maximum allowed size a single file can be when uploaded with the transfer form. The
    size is expressed in **MiB**, *not* MB.

    If the :ref:`FILE_UPLOAD_ENABLED` setting is disabled, this option has no effect.

    **.env Example:**

    ::

        #file: .env
        MAX_SINGLE_UPLOAD_SIZE=512


MAX_TOTAL_UPLOAD_SIZE
^^^^^^^^^^^^^^^^^^^^^

    *Choose the maximum total size (in MiB) of a file transfer*

    .. table::

        ========  ============  =========  ==================  =========================
        Required  Default       Type       Can be set in .env  Can be set in settings.py
        ========  ============  =========  ==================  =========================
        NO        256           int        YES                 YES
        ========  ============  =========  ==================  =========================

    Sets the maximum allowed total size of all files being transferred at one time. The size is
    expressed in **MiB**, *not* MB.

    If the :ref:`FILE_UPLOAD_ENABLED` setting is disabled, this option has no effect.

    **.env Example:**

    ::

        #file: .env
        MAX_TOTAL_UPLOAD_SIZE=1024


MAX_TOTAL_UPLOAD_COUNT
^^^^^^^^^^^^^^^^^^^^^^

    *Choose the maximum number of files can be transferred*

    .. table::

        ========  ============  =========  ==================  =========================
        Required  Default       Type       Can be set in .env  Can be set in settings.py
        ========  ============  =========  ==================  =========================
        NO        40            int        YES                 YES
        ========  ============  =========  ==================  =========================

    Sets the maximum number of files that can be transferred at one time with the transfer form.

    If the :ref:`FILE_UPLOAD_ENABLED` setting is disabled, this option has no effect.

    **.env Example:**

    ::

        #file: .env
        MAX_TOTAL_UPLOAD_COUNT=10


Storage Locations
-----------------


BAG_STORAGE_FOLDER
^^^^^^^^^^^^^^^^^^

    *Choose where BagIt bags are stored*

    .. table::

        ========  =======  =========  ==================  =========================
        Required  Default  Type       Can be set in .env  Can be set in settings.py
        ========  =======  =========  ==================  =========================
        YES                string     YES                 YES
        ========  =======  =========  ==================  =========================

    The folder on the server where bags are to be stored.

    **.env Example:**

    ::

        #file: .env
        BAG_STORAGE_FOLDER=/path/to/your/folder


UPLOAD_STORAGE_FOLDER
^^^^^^^^^^^^^^^^^^^^^

    *Choose storage location for uploaded files*

    .. table::

        ========  ============  =========  ==================  =========================
        Required  Default       Type       Can be set in .env  Can be set in settings.py
        ========  ============  =========  ==================  =========================
        YES                     string     YES                 YES
        ========  ============  =========  ==================  =========================

    The files users upload will be copied here after being uploaded with either of the Django
    file upload handlers. Uploaded files will first be uploaded in memory or to a temporary file
    before being moved to the UPLOAD_STORAGE_FOLDER.

    **.env Example:**

    ::

        #file: .env
        UPLOAD_STORAGE_FOLDER=/path/to/upload/folder


Checksums
---------


BAG_CHECKSUMS
^^^^^^^^^^^^^

    *Choose the checksum algorithms used to create BagIt manifests*

    .. table::

        ========  =======  =========  ==================  =========================
        Required  Default  Type       Can be set in .env  Can be set in settings.py
        ========  =======  =========  ==================  =========================
        NO        sha512   str        YES                 YES - Use with caution
        ========  =======  =========  ==================  =========================

    When BagIt is run, the selected algorithm(s) are used to generate manifests for the files as
    well as the tag files in the Bag. Multiple algorithms can be used, separated by commas. Avoid
    setting these algorithms directly in :code:`settings.py`, as there is some pre-processing of the
    selected algorithms needed to make sure they're formatted correctly.


    **.env Example:**

    ::

        #file: .env
        BAG_CHECKSUMS=sha1,blake2b,md5


Emailing
--------


ARCHIVIST_EMAIL
^^^^^^^^^^^^^^^

    *Choose contact email address*

    .. table::

        ========  =======  =========  ==================  =========================
        Required  Default  Type       Can be set in .env  Can be set in settings.py
        ========  =======  =========  ==================  =========================
        YES                string     YES                 YES
        ========  =======  =========  ==================  =========================

    The email displayed for people to contact an archivist.

    **.env Example:**

    ::

        #file: .env
        ARCHIVIST_EMAIL=archives@domain.ca


DO_NOT_REPLY_USERNAME
^^^^^^^^^^^^^^^^^^^^^

    *Choose username for do not reply emails*

    .. table::

        ========  ============  =========  ==================  =========================
        Required  Default       Type       Can be set in .env  Can be set in settings.py
        ========  ============  =========  ==================  =========================
        NO        do-not-reply  string     YES                 YES
        ========  ============  =========  ==================  =========================

    A username for the application to send "do not reply" emails from. This username is combined
    with the site's base URL to create an email address. The URL can be set from the admin site.

    **.env Example:**

    ::

        #file: .env
        DO_NOT_REPLY_USERNAME=donotreply


ClamAV Virus Checking
---------------------

These settings have no effect is :ref:`CLAMAV_ENABLED` is False, or if :ref:`FILE_UPLOAD_ENABLED` is
False.


CLAMAV_HOST
^^^^^^^^^^^

    *Hostname of ClamAV instance*

    .. table::

        ========  ===============  =========  ==================  =========================
        Required  Default          Type       Can be set in .env  Can be set in settings.py
        ========  ===============  =========  ==================  =========================
        YES       None             string     YES                 YES
        ========  ===============  =========  ==================  =========================

    Hostname of the server running ClamAV.

    If the :ref:`FILE_UPLOAD_ENABLED` setting is disabled, this option has no effect.

    **.env Example:**

    ::

        #file: .env
        CLAMAV_HOST='example.server.org'


CLAMAV_PORT
^^^^^^^^^^^

    *Port of ClamAV instance*

    .. table::

        ========  ===============  =========  ==================  =========================
        Required  Default          Type       Can be set in .env  Can be set in settings.py
        ========  ===============  =========  ==================  =========================
        YES       3310             int        YES                 YES
        ========  ===============  =========  ==================  =========================

    Port of the Clamd instance on the server running ClamAV.

    If the :ref:`FILE_UPLOAD_ENABLED` setting is disabled, this option has no effect.

    **.env Example:**

    ::

        #file: .env
        CLAMAV_PORT=8181


Data Formatting
---------------


APPROXIMATE_DATE_FORMAT
^^^^^^^^^^^^^^^^^^^^^^^

    *Choose estimated date format*

    .. table::

        ========  ======================  =========  ==================  =========================
        Required  Default                 Type       Can be set in .env  Can be set in settings.py
        ========  ======================  =========  ==================  =========================
        NO        :code:`'[ca. {date}]'`  string     YES                 YES
        ========  ======================  =========  ==================  =========================

    A format string for the date to indicate an approximate date. The string variable :code:`{date}`
    must be present for the date format to be used.

    **.env Example:**

    ::

        #file: .env
        APPROXIMATE_DATE_FORMAT='Circa. {date}'


DEFAULT_DATA
^^^^^^^^^^^^

    *Choose default form data*

    .. table::

        ========  ===============  =========  ==================  =========================
        Required  Default          Type       Can be set in .env  Can be set in settings.py
        ========  ===============  =========  ==================  =========================
        NO        See settings.py  dict       NO                  YES
        ========  ===============  =========  ==================  =========================

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

    **settings.py Example:**

    .. code-block:: python

        #file: settings.py
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


CAAIS_UNKNOWN_DATE_TEXT
^^^^^^^^^^^^^^^^^^^^^^^

    *Change the "Unknown date" text*

    .. table::

        ========  ======================  =========  ==================  =========================
        Required  Default                 Type       Can be set in .env  Can be set in settings.py
        ========  ======================  =========  ==================  =========================
        NO        Unknown date            string     YES                 NO
        ========  ======================  =========  ==================  =========================

    A string to use in the CAAIS metadata when a user indicates that a date is not known.

    **.env Example:**

    ::

        #file: .env
        CAAIS_UNKNOWN_DATE_TEXT='Not known'


CAAIS_UNKNOWN_START_DATE
^^^^^^^^^^^^^^^^^^^^^^^^

    *Change the unknown start date*

    .. table::

        ========  ======================  =========  ==================  =========================
        Required  Default                 Type       Can be set in .env  Can be set in settings.py
        ========  ======================  =========  ==================  =========================
        NO        1800-01-01              string     YES                 NO
        ========  ======================  =========  ==================  =========================

    A yyyy-mm-dd formatted date that is used for the start of a date range when an unknown date is
    encountered when parsing a date for CAAIS.

    **.env Example:**

    ::

        #file: .env
        CAAIS_UNKNOWN_START_DATE='1900-01-01'


CAAIS_UNKNOWN_END_DATE
^^^^^^^^^^^^^^^^^^^^^^

    *Change the unknown end date*

    .. table::

        ========  ======================  =========  ==================  =========================
        Required  Default                 Type       Can be set in .env  Can be set in settings.py
        ========  ======================  =========  ==================  =========================
        NO        2010-01-01              string     YES                 NO
        ========  ======================  =========  ==================  =========================

    A yyyy-mm-dd formatted date that is used for the end of a date range when an unknown date is
    encountered when parsing a date for CAAIS.

    **.env Example:**

    ::

        #file: .env
        CAAIS_UNKNOWN_END_DATE='1999-12-31'
