Accepted File Types
===================

The types of files that can be uploaded with the transfer form are defined in a Python variable in
the file :code:`bagitobjecttransfer/recordtransfer/settings.py`. You can also see this variable on
the about page (accessible at /about/).

This is what the variable might look like:

.. code-block:: python

    ACCEPTED_FILE_FORMATS = {
        'Archive': [
            'zip',
        ],
        'Document': [
            'doc',
            'docx',
            'pdf',
        ],
        'Photo': [
            'jpg',
            'jpeg',
            'png',
        ],
    }


The keys of the Python dictionary (Archive, Document, Photo) indicate the general type of file. The
list for each file type indicates what types of files are considered to be in that group. If a user
tries to upload a file that doesn't have an extension listed for any of the groups, they will not be
able to upload that file. Using the above settings, you would not be able to upload a music MP3
file, because **mp3** is not listed anywhere.

If you want users to be able to only upload spreadsheets and documents, you might use this
structure:

.. code:: python

    ACCEPTED_FILE_FORMATS = {
        'Spreadsheet': [
            'xlsx',
            'xls',
            'xlsb',
            'ods',
        ],
        'Document': [
            'docx',
            'doc',
            'pdf',
            'odt',
        ]
    }


If you want to get really specific, you could also do this:

.. code:: python

    ACCEPTED_FILE_FORMATS = {
        # Spreadsheets
        'Excel Workbook': ['xlsx'],
        'Excel Macro Workbook': ['xlsm'],
        'Excel Binary Workbook': ['xlsb'],
        'Excel 1997-2003 Workbook': ['xls'],
        'OpenDocument Spreadsheet': ['ods'],

        # Documents
        'Word Document': ['docx'],
        'Word 1997-2003 Document': ['doc'],
        'OpenDocument Text': ['odt'],

        # PDFs
        'Adobe PDF': ['pdf']
    }


Setting this up will vary on how granular your institution wants to be with capturing file types.

.. warning::

    If you are creating groups of files, be sure to name them in a *singular* form. Do not give a
    group the name "Spreadsheets," because the application will add an "s" to the name of the group
    if there are multiple files of that type uploaded.

    You must also list the extensions in lower case, without a period. Do not write ".mp3" or the
    file type will not be recognized.
