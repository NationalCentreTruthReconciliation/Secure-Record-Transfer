Application Settings
====================

.. automodule:: recordtransfer.settings
   :members:

These settings control the behaviour of the application. 99% of options can be controlled by setting
a value in a :code:`.dev.env` or :code:`.prod.env` file, depending on whether you're running the dev
or prod configuration. This file is referred to as :code:`.env` below.

.. contents:: List of Settings


Application Features
--------------------


MAX_SAVED_TRANSFER_COUNT
^^^^^^^^^^^^^^^^^^^^^^^^

    *Choose maximum saved transfers per user*

    .. table::

        ========  ======================  =========
        Required  Default                 Type
        ========  ======================  =========
        NO        2                       int
        ========  ======================  =========

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

        ========  ============  =========
        Required  Default       Type
        ========  ============  =========
        NO        True          bool
        ========  ============  =========

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

        ========  ============  =========
        Required  Default       Type
        ========  ============  =========
        NO        True          bool
        ========  ============  =========

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

      ========  ============  =========
      Required  Default       Type
      ========  ============  =========
      NO        True          bool
      ========  ============  =========

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

      ========  ============  =========
      Required  Default       Type
      ========  ============  =========
      NO        False         bool
      ========  ============  =========

  It is possible to enable this setting so that site templates can be changed without having to
  re-deploy the application. Be careful with enabling this - it is very easy to break templates,
  hence why it is **disabled** by default.

  **.env Example:**

  ::

      #file: .env
      DBTEMPLATES_ENABLED=false


Services
--------

These settings control connections to services external to the Django application. This include:

- `ClamAV <https://www.clamav.net/>`_ for virus checking
- `MySQL <https://www.mysql.com/>`_ Database
- `Redis <https://redis.io/>`_ task broker

CLAMAV_ENABLED
^^^^^^^^^^^^^^

    *Whether ClamAV malware checking is enabled*

    .. table::

        ========  ===============  =========
        Required  Default          Type
        ========  ===============  =========
        NO        True             bool
        ========  ===============  =========

    Enables/disables whether ClamAV malware checking is enabled.

    If the :ref:`FILE_UPLOAD_ENABLED` setting is disabled, this option has no effect.

    **.env Example:**

    ::

        #file: .env
        CLAMAV_ENABLED=True


CLAMAV_HOST
^^^^^^^^^^^

    *The name of the host ClamAV is running on*

    .. table::

        ===========  ===============  =========
        Required     Default          Type
        ===========  ===============  =========
        NO           clamav           string
        ===========  ===============  =========

    Chooses the host where ClamAV is running. If :ref:`CLAMAV_ENABLED` is FALSE, this setting does
    not have any effect.

    **.env Example:**

    ::

        #file: .env
        CLAMAV_HOST=clamav


CLAMAV_PORT
^^^^^^^^^^^

    *The port ClamAV is running on*

    .. table::

        ===========  ===============  =========
        Required     Default          Type
        ===========  ===============  =========
        NO           3310             int
        ===========  ===============  =========

    Chooses the port where ClamAV is accessible on the :ref:`CLAMAV_HOST`. If :ref:`CLAMAV_ENABLED`
    is FALSE, this setting does not have any effect.

    **.env Example:**

    ::

        #file: .env
        CLAMAV_PORT=3310


REDIS_HOST
^^^^^^^^^^

    *The name of the host Redis is running on*

    .. table::

        ===========  ===============  =========
        Required     Default          Type
        ===========  ===============  =========
        NO           redis            string
        ===========  ===============  =========

    Chooses the host where Redis is running. Redis is used in tandem with RQ to store ephemeral info
    about asynchronous jobs.

    **.env Example:**

    ::

        #file: .env
        REDIS_HOST=my-redis


REDIS_PORT
^^^^^^^^^^

    *The port Redis is running on*

    .. table::

        ===========  ===============  =========
        Required     Default          Type
        ===========  ===============  =========
        NO           6379             int
        ===========  ===============  =========

    Chooses the port where Redis is accessible on the :ref:`REDIS_HOST`.

    **.env Example:**

    ::

        #file: .env
        REDIS_PORT=6379


REDIS_PASSWORD
^^^^^^^^^^^^^^

    *The password required to connect to Redis*

    .. table::

        ===========  ===============  =========
        Required     Default          Type
        ===========  ===============  =========
        NO           ""               string
        ===========  ===============  =========

    By default, Redis **does not require a password**. If you would prefer to set one up, you can,
    and then use this setting to control the password. The default empty value is fine if you are
    using the application's default Redis configuration.

    **.env Example:**

    ::

        #file: .env
        REDIS_PASSWORD=a-strong-password-here


File Upload Controls
--------------------

These settings have no effect if :ref:`FILE_UPLOAD_ENABLED` is False.


ACCEPTED_FILE_FORMATS
^^^^^^^^^^^^^^^^^^^^^

    *Choose what files (by extension) can be uploaded*

    .. table::

        ========  ===============  =========
        Required  Default          Type
        ========  ===============  =========
        NO        See below        str
        ========  ===============  =========

    Accepted files are grouped by type of file. The default accepted file extensions are:

    - Archive
        - zip
    - Audio
        - mp3
        - wav
        - flac
    - Document
        - docx
        - odt
        - pdf
        - txt
        - html
    - Image
        - jpg
        - jpeg
        - png
        - gif
    - Spreadsheet
        - xlsx
        - csv
    - Video
        - mkv
        - mp4

    This setting has a special structured syntax, that looks like:

    ::

        File Group Name:ext,ext,ext|Other Group Name:ext,ext


    File extensions are grouped by name. File groups are split by the pipe | character, and file
    extensions are split by comma.

    The file extensions are used to determine what a user is allowed to upload. The group name is
    used to create a human-readable extent statement about the quantity and type of files the user
    uploaded.

    If the :ref:`FILE_UPLOAD_ENABLED` setting is disabled, this option has no effect.

    Here are some examples based on what you might want to accept (note that you can only specify
    the ACCEPTED_FILE_FORMATS variable *once*):

    ::

        #file: .env

        # Only PDFs
        ACCEPTED_FILE_FORMATS="PDF:pdf"

        # Audio or Video
        ACCEPTED_FILE_FORMATS="Audio:mp3,wav|Video:mkv,mp4"

        # Excel spreadsheets
        ACCEPTED_FILE_FORMATS="Excel Workbook:xlsx|Excel Macro Workbook:xlsm|Excel 1997-2003 Workbook:xls"

        # Images and documents
        ACCEPTED_FILE_FORMATS="PDF:pdf,docx,txt|Image:jpeg,jpg,png,gif,tif,tiff"



MAX_SINGLE_UPLOAD_SIZE
^^^^^^^^^^^^^^^^^^^^^^

    *Choose the maximum size (in MiB) an uploaded file is allowed to be*

    .. table::

        ========  ============  =========
        Required  Default       Type
        ========  ============  =========
        NO        64            int
        ========  ============  =========

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

        ========  ============  =========
        Required  Default       Type
        ========  ============  =========
        NO        256           int
        ========  ============  =========

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

        ========  ============  =========
        Required  Default       Type
        ========  ============  =========
        NO        40            int
        ========  ============  =========

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

        ========  =======  =========
        Required  Default  Type
        ========  =======  =========
        YES                string
        ========  =======  =========

    The folder on the server where bags are to be stored.

    **.env Example:**

    ::

        #file: .env
        BAG_STORAGE_FOLDER=/path/to/your/folder


UPLOAD_STORAGE_FOLDER
^^^^^^^^^^^^^^^^^^^^^

    *Choose storage location for uploaded files*

    .. table::

        ========  ============  =========
        Required  Default       Type
        ========  ============  =========
        YES                     string
        ========  ============  =========

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

        ========  =======  =========
        Required  Default  Type
        ========  =======  =========
        NO        sha512   str
        ========  =======  =========

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

        ========  =======  =========
        Required  Default  Type
        ========  =======  =========
        YES                string
        ========  =======  =========

    The email displayed for people to contact an archivist.

    **.env Example:**

    ::

        #file: .env
        ARCHIVIST_EMAIL=archives@domain.ca


DO_NOT_REPLY_USERNAME
^^^^^^^^^^^^^^^^^^^^^

    *Choose username for do not reply emails*

    .. table::

        ========  ============  =========
        Required  Default       Type
        ========  ============  =========
        NO        do-not-reply  string
        ========  ============  =========

    A username for the application to send "do not reply" emails from. This username is combined
    with the site's base URL to create an email address. The URL can be set from the admin site.

    **.env Example:**

    ::

        #file: .env
        DO_NOT_REPLY_USERNAME=donotreply


Data Formatting and Defaults
----------------------------

The following variables control how metadata is formatted, as well as defines default values to use
when generating CAAIS metadata a value is not specified in the form. By leaving default values
empty, they are not used.


APPROXIMATE_DATE_FORMAT
^^^^^^^^^^^^^^^^^^^^^^^

    *Choose estimated date format*

    .. table::

        ========  ======================  =========
        Required  Default                 Type
        ========  ======================  =========
        NO        :code:`'[ca. {date}]'`  string
        ========  ======================  =========

    A format string for the date to indicate an approximate date. The string variable :code:`{date}`
    must be present for the date format to be used.

    **.env Example:**

    ::

        #file: .env
        APPROXIMATE_DATE_FORMAT='Circa. {date}'


CAAIS_UNKNOWN_DATE_TEXT
^^^^^^^^^^^^^^^^^^^^^^^

    *Change the "Unknown date" text*

    .. table::

        ========  ======================  =========
        Required  Default                 Type
        ========  ======================  =========
        NO        Unknown date            string
        ========  ======================  =========

    A string to use in the CAAIS metadata when a user indicates that a date is not known.

    **.env Example:**

    ::

        #file: .env
        CAAIS_UNKNOWN_DATE_TEXT='Not known'


CAAIS_UNKNOWN_START_DATE
^^^^^^^^^^^^^^^^^^^^^^^^

    *Change the unknown start date*

    .. table::

        ========  ======================  =========
        Required  Default                 Type
        ========  ======================  =========
        NO        1800-01-01              string
        ========  ======================  =========

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

        ========  ======================  =========
        Required  Default                 Type
        ========  ======================  =========
        NO        2010-01-01              string
        ========  ======================  =========

    A yyyy-mm-dd formatted date that is used for the end of a date range when an unknown date is
    encountered when parsing a date for CAAIS.

    **.env Example:**

    ::

        #file: .env
        CAAIS_UNKNOWN_END_DATE='1999-12-31'


CAAIS_DEFAULT_REPOSITORY
^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 1.1 - Repository*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    **.env Example:**

    ::

        # file .env
        CAAIS_DEFAULT_REPOSITORY='Archives'


CAAIS_DEFAULT_ACCESSION_TITLE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 1.3 - Accession Title*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    **.env Example:**

    ::

        # file .env
        CAAIS_DEFAULT_ACCESSION_TITLE='No Title'


CAAIS_DEFAULT_ARCHIVAL_UNIT
^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 1.4 - Archival Unit*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    While the Archival Unit field *is* repeatable in CAAIS, it is not possible to specify
    multiple archival unit defaults.

    ::

        # file .env
        CAAIS_DEFAULT_ARCHIVAL_UNIT='Archival Unit'


CAAIS_DEFAULT_ACQUISITION_METHOD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 1.5 - Acquisition Method*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    ::

        # file .env
        CAAIS_DEFAULT_ACQUISITION_METHOD='Digital Transfer'


CAAIS_DEFAULT_DISPOSITION_AUTHORITY
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 1.6 - Disposition Authority*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    While the Disposition Authority field *is* repeatable, it is not possible to specify multiple
    disposition authority defaults.

    ::

        # file .env
        CAAIS_DEFAULT_DISPOSITION_AUTHORITY='Default value'


CAAIS_DEFAULT_STATUS
^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 1.7 - Status*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    Leave empty, or populate with a term like "Waiting for review" to signify that the metadata has
    not been reviewed yet.

    ::

        # file .env
        CAAIS_DEFAULT_STATUS='Not Reviewed'


CAAIS_DEFAULT_SOURCE_CONFIDENTIALITY
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 2.1.6 - Source Confidentiality*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If a default is supplied, the source confidentiality will be applied to every source of material
    received.

    ::

        # file .env
        CAAIS_DEFAULT_SOURCE_CONFIDENTIALITY='Anonymous'


CAAIS_DEFAULT_PRELIMINARY_CUSTODIAL_HISTORY
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 2.2 - Preliminary Custodial History*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    While the Preliminary Custodial History field *is* repeatable in CAAIS, it is not possible to
    specify multiple defaults here.

    ::

        # file .env
        CAAIS_DEFAULT_PRELIMINARY_CUSTODIAL_HISTORY='Default value'


CAAIS_DEFAULT_DATE_OF_MATERIALS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 3.1 - Date of Materials*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    See also: :ref:`CAAIS_UNKNOWN_DATE_TEXT`.

    ::

        # file .env
        CAAIS_DEFAULT_DATE_OF_MATERIALS='Unknown date'


CAAIS_DEFAULT_EXTENT_TYPE
^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 3.2.1 - Extent Type*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If a default is supplied, the extent type will be applied to every extent statement received.

    ::

        # file .env
        CAAIS_DEFAULT_EXTENT_TYPE='Extent received'


CAAIS_DEFAULT_QUANTITY_AND_UNIT_OF_MEASURE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 3.2.2 - Quantity and Unit of Measure*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If a default is supplied, the quantity and unit of measure will be applied to every extent
    statement received.

    ::

        # file .env
        CAAIS_DEFAULT_QUANTITY_AND_UNIT_OF_MEASURE='No files'


CAAIS_DEFAULT_CONTENT_TYPE
^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 3.2.3 - Content Type*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If a default is supplied, the content type will be applied to every extent statement received.

    ::

        # file .env
        CAAIS_DEFAULT_CONTENT_TYPE='Digital files'


CAAIS_DEFAULT_CARRIER_TYPE
^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 3.2.4 - Carrier Type*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If a default is supplied, the carrier type will be applied to every extent statement received.

    ::

        # file .env
        CAAIS_DEFAULT_CARRIER_TYPE='N/A'


CAAIS_DEFAULT_EXTENT_NOTE
^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 3.2.5 - Extent Note*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If a default is supplied, the extent note will be applied to every extent statement received.

    ::

        # file .env
        CAAIS_DEFAULT_EXTENT_NOTE='Extent provided by submitter'


CAAIS_DEFAULT_PRELIMINARY_SCOPE_AND_CONTENT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 3.3 - Preliminary Scope and Content*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    While the Preliminary Scope and Content field *is* repeatable in CAAIS, it is not possible to
    specify multiple defaults here.

    ::

        # file .env
        CAAIS_DEFAULT_PRELIMINARY_SCOPE_AND_CONTENT='No scope and content received.'


CAAIS_DEFAULT_LANGUAGE_OF_MATERIAL
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 3.4*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    ::

        # file .env
        CAAIS_DEFAULT_LANGUAGE_OF_MATERIAL='Default'


CAAIS_DEFAULT_STORAGE_LOCATION
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 4.1*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    ::

        # file .env
        CAAIS_DEFAULT_STORAGE_LOCATION='Default'


CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_TYPE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 4.3.1*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If not empty, a default preservation requirements statement will be applied to each submission.

    ::

        # file .env
        CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_TYPE='Default'


CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_VALUE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 4.3.2*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If not empty, a default preservation requirements statement will be applied to each submission.

    ::

        # file .env
        CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_VALUE='Default'


CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_NOTE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 4.3.3*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If not empty, a default preservation requirements statement will be applied to each submission.

    ::

        # file .env
        CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_NOTE='Default'


CAAIS_DEFAULT_APPRAISAL_TYPE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 4.4.1*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If not empty, a default appraisal statement will be applied to each submission.

    ::

        # file .env
        CAAIS_DEFAULT_APPRAISAL_TYPE='Default'


CAAIS_DEFAULT_APPRAISAL_VALUE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 4.4.2*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If not empty, a default appraisal statement will be applied to each submission.

    ::

        # file .env
        CAAIS_DEFAULT_APPRAISAL_VALUE='Default'


CAAIS_DEFAULT_APPRAISAL_NOTE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 4.4.3*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If not empty, a default appraisal statement will be applied to each submission.

    ::

        # file .env
        CAAIS_DEFAULT_APPRAISAL_NOTE='Default'


CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TYPE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 4.5.1*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If not empty, a default associated document will be applied to each submission.

    ::

        # file .env
        CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TYPE='Default'


CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TITLE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 4.5.2*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If not empty, a default associated document will be applied to each submission.

    ::

        # file .env
        CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TITLE='Default'


CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_NOTE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 4.5.3*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    If not empty, a default associated document will be applied to each submission.

    ::

        # file .env
        CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_NOTE='Default'


CAAIS_DEFAULT_GENERAL_NOTE
^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 6.1*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    ::

        # file .env
        CAAIS_DEFAULT_GENERAL_NOTE='Default'


CAAIS_DEFAULT_RULES_OR_CONVENTIONS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 7.1*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    ::

        # file .env
        CAAIS_DEFAULT_RULES_OR_CONVENTIONS='CAAIS v1.0'


CAAIS_DEFAULT_LANGUAGE_OF_ACCESSION_RECORD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default value to fill in metadata for CAAIS sec. 7.3*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    ::

        # file .env
        CAAIS_DEFAULT_LANGUAGE_OF_ACCESSION_RECORD='en'


CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default submission event type name - related to CAAIS sec. 5.1.1*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        YES       Transfer Submitted   string
        ========  ===================  =========

    At the time of receiving a submission, a "Submission" type event is created for the submission.
    You can control the Event Type name for that event here.

    ::

        # file .env
        CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE='Default'


CAAIS_DEFAULT_SUBMISSION_EVENT_AGENT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default submission event agent - related to CAAIS sec. 5.1.3*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    At the time of receiving a submission, a "Submission" type event is created for the submission.
    You can control the Event Agent's name for that event here.

    ::

        # file .env
        CAAIS_DEFAULT_SUBMISSION_EVENT_AGENT='Transfer Application'


CAAIS_DEFAULT_SUBMISSION_EVENT_NOTE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default submission event note - related to CAAIS sec. 5.1.4*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    At the time of receiving a submission, a "Submission" type event is created for the submission.
    You can control whether an Event Note is added for the event here.

    ::

        # file .env
        CAAIS_DEFAULT_SUBMISSION_EVENT_NOTE='Transfer submitted via record transfer application'


CAAIS_DEFAULT_CREATION_TYPE
^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default date of creation event name - related to CAAIS sec. 7.2.1*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        YES       Creation             string
        ========  ===================  =========

    At the time of receiving a submission, a Date of Creation or Revision is created to indicate
    the date the accession record was created. You can control the name of the event here if you do
    not want to call it "Creation".

    ::

        # file .env
        CAAIS_DEFAULT_CREATION_TYPE='Record Created'


CAAIS_DEFAULT_CREATION_AGENT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default date of creation event agent - related to CAAIS sec. 7.2.3*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    At the time of receiving a submission, a Date of Creation or Revision is created to indicate
    the date the accession record was created. You can control the name of the event agent here.

    ::

        # file .env
        CAAIS_DEFAULT_CREATION_AGENT='Transfer Application'


CAAIS_DEFAULT_CREATION_NOTE
^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default date of creation event note - related to CAAIS sec. 7.2.4*

    .. table::

        ========  ===================  =========
        Required  Default              Type
        ========  ===================  =========
        NO        "" *(empty string)*  string
        ========  ===================  =========

    At the time of receiving a submission, a Date of Creation or Revision is created to indicate
    the date the accession record was created. You can add a note to that event here by setting the
    value to something other than an empty string.

    ::

        # file .env
        CAAIS_DEFAULT_CREATION_NOTE='Defaults filled automatically by application.'