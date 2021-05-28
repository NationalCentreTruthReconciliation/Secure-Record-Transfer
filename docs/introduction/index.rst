Introduction
============

This application exists primarily to simplify and standardize the transfer and accessioning of
digital records. As archives begin to hold more digital material, it is becoming important to
digitize the workflows involved in maintaining the archives. A large amount of records created
nowadays are "born-digital," material that was created first in digital form. This app facilitates
the process of sending digital records to an archive, as well as packaging the material and its
associated metadata in a standardized way for archivists to view.

This application makes use of two specifications:

* `BagIt <https://tools.ietf.org/html/rfc8493>`_
* `Canadian Archival Accession Information Standard <http://archivescanada.ca/CWG_AccessionStandard>`_

BagIt is a file packaging specification that describes a way to securely package a number of files
and their associated metadata. In this project, we are using the Python implementation of BagIt,
`bagit-python <https://github.com/LibraryOfCongress/bagit-python>`_.

The Canadian Archival Accession Information Standard (CAAIS) aims to standard the metadata supplied
for an accession. The main transfer form in this app contains many of the fields in that
specification, some have been given a new name in the form to make it easier for a user to
understand, but the metadata and reports generated all use the fields in CAAIS verbatim.

What Does this App Do?
######################

Foremost, this app provides a multi-page transfer form with CAAIS-oriented fields and a file upload
space for users. The transfer form is filled out by users who want to transfer material to the
archive.

This application also provides an administrator website for archivists and administrators. Some of
the functions you can do with the administrator site are:

* Generate HTML metadata reports for 1 or more generated Bags
* Export CSV information about 1 or more generated Bags
* Set the "Review Status" of a Bag
* Make decisions about the accession
* Manage user accounts
