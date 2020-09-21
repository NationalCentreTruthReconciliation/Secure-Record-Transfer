# BagIt Transfer Portal

Please, [read the docs!](https://nctr-bagit-record-transfer.readthedocs.io/en/)

A file transfer application made for securely transferring files over the internet and securing them in a BagIt bag for archivists to view. The CAAIS is observed in this application, and a large portion of the metadata fields specified in that document are present in this application's transfer form.

With the user-side application, users provide a detailed description of the files they wish to transfer in a series of forms, and upload their files securely to a server. After they upload their files, they are packaged into a Bag. The Bag contains all of the uploaded files, all the metadata that was entered, and checksums to ensure the integrity of the files and metadata.

The created bags are available for archivists to view and ingest into whatever archival system they use. An easy-to-read HTML report is also generated for each bag so an archivist can easily see what sort of metadata the user entered when they transferred their files. Using the built-in administrator application, an archivist can do any of the following useful operations:

- View high-level info for all transferred bags
- View an HTML report for a bag
- Export metadata reports for the bags in a zip file
- Export a CSV containing the paths to where the bags are located on the server
- Change the "Review Status" of a bag
