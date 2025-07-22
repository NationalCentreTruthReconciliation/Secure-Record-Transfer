Application Settings
====================

These settings control the behaviour of the application in addition to the default Django settings.
Depending on whether you're running the dev or prod configuration, settings can be changed in the
:code:`.dev.env` or :code:`.prod.env` file, respectively. This file is referred to as :code:`.env`
below.

.. contents:: List of Settings


Security
--------

SECRET_KEY
^^^^^^^^^^

    *Django's secret key for cryptographic signing*

    .. table::

        =======================  =========
        Default                  Type
        =======================  =========
        Development key only     string
        =======================  =========

    The SECRET_KEY is a critical security setting used by Django for cryptographic signing, including:

    - Session security and CSRF protection
    - Password reset tokens and user authentication
    - Secure cookies and form validation
    - Digital signatures for sensitive data

    In development, a default key is provided for convenience, but **you must set a strong, unique SECRET_KEY for production deployments**. The application will fail to start in production without this setting.

    **.env Example:**

    ::

        # file: .prod.env
        SECRET_KEY=your-very-long-random-secret-key-with-letters-numbers-and-symbols

    **Generating a Strong Secret Key:**

    You can generate a secure SECRET_KEY using Python:

    ::

        python -c "import secrets; print(secrets.token_urlsafe(50))"


Application Features
--------------------


SIGN_UP_ENABLED
^^^^^^^^^^^^^^^

    *Choose whether new users can sign up*

    .. table::

        ============  =========
        Default       Type
        ============  =========
        True          bool
        ============  =========

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

        ============  =========
        Default       Type
        ============  =========
        True          bool
        ============  =========

    Sets whether file uploads are allowed. If they are *not* allowed (disabled), then only metadata
    is submitted to the application.

    **.env Example:**

    ::

        #file: .env
        FILE_UPLOAD_ENABLED=false


USE_DATE_WIDGETS
^^^^^^^^^^^^^^^^

  *Use JavaScript date widgets*

  .. table::

      ============  =========
      Default       Type
      ============  =========
      True          bool
      ============  =========

  If set to True, a date picker widget is used for date fields. If set to False, input text
  fields with an input mask are used instead.

  **.env Example:**

  ::

      #file: .env
      USE_DATE_WIDGETS=false


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

        ===============  =========
        Default          Type
        ===============  =========
        True             bool
        ===============  =========

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

        ===============  =========
        Default          Type
        ===============  =========
        clamav           string
        ===============  =========

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

        ===============  =========
        Default          Type
        ===============  =========
        3310             int
        ===============  =========

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

        ===============  =========
        Default          Type
        ===============  =========
        redis            string
        ===============  =========

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

        ===============  =========
        Default          Type
        ===============  =========
        6379             int
        ===============  =========

    Chooses the port where Redis is accessible on the :ref:`REDIS_HOST`.

    **.env Example:**

    ::

        #file: .env
        REDIS_PORT=6379


REDIS_PASSWORD
^^^^^^^^^^^^^^

    *The password required to connect to Redis*

    .. table::

        ===============  =========
        Default          Type
        ===============  =========
        ""               string
        ===============  =========

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

        ===============  =======================
        Default          Type
        ===============  =======================
        See below        string (special syntax)
        ===============  =======================

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



MAX_SINGLE_UPLOAD_SIZE_MB
^^^^^^^^^^^^^^^^^^^^^^^^^

    *Choose the maximum size (in MB) an uploaded file is allowed to be*

    .. table::

        ============  =========
        Default       Type
        ============  =========
        64            int
        ============  =========

    Sets the maximum allowed size a single file can be when uploaded with the transfer form. The
    size is expressed in **MB**, *not* MiB.

    If the :ref:`FILE_UPLOAD_ENABLED` setting is disabled, this option has no effect.

    **.env Example:**

    ::

        #file: .env
        MAX_SINGLE_UPLOAD_SIZE_MB=512


MAX_TOTAL_UPLOAD_SIZE_MB
^^^^^^^^^^^^^^^^^^^^^^^^

    *Choose the maximum total size (in MB) of a file transfer*

    .. table::

        ============  =========
        Default       Type
        ============  =========
        256           int
        ============  =========

    Sets the maximum allowed total size of all files being transferred at one time. The size is
    expressed in **MB**, *not* MiB.

    If the :ref:`FILE_UPLOAD_ENABLED` setting is disabled, this option has no effect.

    **.env Example:**

    ::

        #file: .env
        MAX_TOTAL_UPLOAD_SIZE_MB=1024


MAX_TOTAL_UPLOAD_COUNT
^^^^^^^^^^^^^^^^^^^^^^

    *Choose the maximum number of files can be transferred*

    .. table::

        ============  =========
        Default       Type
        ============  =========
        40            int
        ============  =========

    Sets the maximum number of files that can be transferred at one time with the transfer form.

    If the :ref:`FILE_UPLOAD_ENABLED` setting is disabled, this option has no effect.

    **.env Example:**

    ::

        #file: .env
        MAX_TOTAL_UPLOAD_COUNT=10

Upload Session Controls
-----------------------

These settings have no effect if :ref:`FILE_UPLOAD_ENABLED` is False.

UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Number of minutes of inactivity after which an upload session expires*

    .. table::

        ============  =========
        Default       Type
        ============  =========
        1440          int
        ============  =========

    Sets the number of minutes of inactivity after which an upload session expires. Defaults to 1440 minutes (24 hours).
    This feature can be deactivated by setting the value to -1.

    **.env Example:**

    ::

        #file: .env
        UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES=1440

UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Number of minutes before upload session expiration when a reminder should be sent*

    .. table::

        ============  =========
        Default       Type
        ============  =========
        480           int
        ============  =========

    Sets the number of minutes before upload session expiration when a reminder should be sent. Defaults to 480 minutes (8 hours).
    This feature can be deactivated by setting the value to -1.
    If :ref:`UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES` is set to -1, this feature will be deactivated.


    **.env Example:**

    ::

        #file: .env
        UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES=480


UPLOAD_SESSION_EXPIRED_CLEANUP_SCHEDULE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Cron schedule expression for cleaning up expired upload sessions*

    .. table::

        ==============  =========
        Default         Type
        ==============  =========
        "0 2 \* \* \*"  string
        ==============  =========

    Sets the cron schedule expression for cleaning up expired upload sessions. Defaults to "0 2 \* \* \*" (runs at 2 AM daily).

    See the `crontab manual page <https://man7.org/linux/man-pages/man5/crontab.5.html>`_ for a guide on the syntax.

    This feature can be deactivated by setting the value to an empty string ("").
    If :ref:`UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES` is set to -1, this feature will be deactivated.

    **.env Example:**

    ::

        #file: .env
        UPLOAD_SESSION_EXPIRED_CLEANUP_SCHEDULE="0 2 * * *"

In-Progress Submission Controls
-------------------------------

IN_PROGRESS_SUBMISSION_EXPIRING_EMAIL_SCHEDULE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Cron schedule expression for sending reminder emails for in-progress submissions with expiring upload sessions*

    .. table::

        ===============  =========
        Default          Type
        ===============  =========
        "0 \* \* \* \*"   string
        ===============  =========

    Sets the cron schedule expression for sending reminder emails for in-progress submissions with expiring upload sessions. Defaults to "0 \* \* \* \*" (runs every hour at minute zero).

    See the `crontab manual page <https://man7.org/linux/man-pages/man5/crontab.5.html>`_ for a guide on the syntax.

    This feature can be deactivated by setting the value to an empty string ("").
    If :ref:`UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES` is set to -1, this feature will be deactivated.

    **.env Example:**

    ::

        #file: .env
        IN_PROGRESS_SUBMISSION_EXPIRING_EMAIL_SCHEDULE="0 * * * *"


Storage Locations
-----------------


UPLOAD_STORAGE_FOLDER
^^^^^^^^^^^^^^^^^^^^^

    *Choose storage location for uploaded files*

    .. table::

        ======================================================  ======================================================  ======
        Default in Dev                                          Default in Prod                                         Type
        ======================================================  ======================================================  ======
        /opt/secure-record-transfer/app/media/uploaded_files/   /opt/secure-record-transfer/app/media/uploaded_files/   string
        ======================================================  ======================================================  ======

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

        =======  ========================
        Default  Type
        =======  ========================
        sha512   string (comma-separated)
        =======  ========================

    When BagIt is run, the selected algorithm(s) are used to generate manifests for the files as
    well as the tag files in the Bag. Multiple algorithms can be used, separated by commas. Avoid
    setting these algorithms directly in :code:`settings.py`, as there is some pre-processing of the
    selected algorithms needed to make sure they're formatted correctly.


    **.env Example:**

    ::

        #file: .env
        BAG_CHECKSUMS=sha1,blake2b,md5


Data Formatting and Defaults
----------------------------

The following variables control how metadata is formatted, as well as defines default values to use
when generating CAAIS metadata a value is not specified in the form. By leaving default values
empty, they are not used.


APPROXIMATE_DATE_FORMAT
^^^^^^^^^^^^^^^^^^^^^^^

    *Choose estimated date format*

    .. table::

        ======================  =========
        Default                 Type
        ======================  =========
        :code:`'[ca. {date}]'`  string
        ======================  =========

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

        ======================  =========
        Default                 Type
        ======================  =========
        Unknown date            string
        ======================  =========

    A string to use in the CAAIS metadata when a user indicates that a date is not known.

    **.env Example:**

    ::

        #file: .env
        CAAIS_UNKNOWN_DATE_TEXT='Not known'


CAAIS_UNKNOWN_START_DATE
^^^^^^^^^^^^^^^^^^^^^^^^

    *Change the unknown start date*

    .. table::

        ======================  =========
        Default                 Type
        ======================  =========
        1800-01-01              string
        ======================  =========

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

        ======================  =========
        Default                 Type
        ======================  =========
        2010-01-01              string
        ======================  =========

    A yyyy-mm-dd formatted date that is used for the end of a date range when an unknown date is
    encountered when parsing a date for CAAIS.

    **.env Example:**

    ::

        #file: .env
        CAAIS_UNKNOWN_END_DATE='1999-12-31'


CAAIS_DEFAULT_UPDATE_TYPE
^^^^^^^^^^^^^^^^^^^^^^^^^

    *Default creation or revision type for metadata updates*

    .. table::

        =======  =========
        Default  Type
        =======  =========
        Update   string
        =======  =========

    When metadata records are updated through the Django admin interface, a DateOfCreationOrRevision entry is automatically created to track changes. This setting controls the name of the creation/revision type used for these updates.

    **.env Example:**

    ::

        #file: .env
        CAAIS_DEFAULT_UPDATE_TYPE='Record Updated'


Testing
-------

SELENIUM_TESTS_HEADLESS_MODE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *Controls whether Selenium tests run in headless mode*

    .. table::

        =======  =========
        Default  Type
        =======  =========
        False    boolean
        =======  =========

    When set to ``True``, Selenium tests will run in headless mode (without a visible browser
    window). This is useful for CI/CD environments or when running tests in the background. When
    ``False``, browser windows will be visible during test execution.

    ::

        # file .env
        SELENIUM_TESTS_HEADLESS_MODE=True

