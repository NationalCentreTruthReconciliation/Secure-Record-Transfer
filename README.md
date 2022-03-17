# Secure Record Transfer Application

Please, [read the docs!](https://nctr-bagit-record-transfer.readthedocs.io/en/latest/)

The secure record transfer application has been designed for the purpose of transferring files and metadata over the internet to an institution before securing the files in a [BagIt](https://datatracker.ietf.org/doc/html/rfc8493) bag. This application attempts to closely follow the [Canadian Archival Accession Information Standard (CAAIS)](http://archivescanada.ca/CWG_AccessionStandard). As such, most of the fields in the Accession Standard are captured when a user submits files and metadata through the application's [transfer form](https://nctr-bagit-record-transfer.readthedocs.io/en/latest/howtouse/transferform.html). A suite of administrative tools is also provided with the app to allow staff members to view, appraise, download, an export submissions made by users.

## AtoM Compatibility

This application is compatible with version 2.x of [AtoM](https://www.accesstomemory.org/en/), an open-source archival access database. Administrators can export an accession CSV from the application's backend, and directly import those CSVs into AtoM to create accession records. **Note** that some fields are dropped in the conversion of CAAIS to AtoM-compliant Accession records, as certain fields in the Accession Standard are not present in the AtoM accession module. This issue is actively being addressed.

## Quickstart

The simplest way to run the application is using Docker. To run the app in this way, ensure you have [Docker Desktop](https://www.docker.com/products/docker-desktop) installed on your system. You will also need [Python 3](https://python.org) and [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).

From a terminal, clone the repository:

```shell
git clone https://github.com/NationalCentreTruthReconciliation/Secure-Record-Transfer.git
```

Enter the `Secure-Record-Transfer/bagitobjecttransfer` directory:

```shell
cd Secure-Record-Transfer/bagitobjecttransfer
```

Create a default `.dockerenv` file and run the application in Docker:

```shell
python manage.py dockerenv
docker-compose up -d
```

After the containers are built, the application should now be accessible at http://localhost:8000. Any emails that are sent by the application are intercepted by the mail application running at http://localhost:8025. If you run into an error the first time your run the app where the MySQL database hasn't been initialized yet, simply restart the application and that should fix the problem. To restart the app:

```shell
docker-compose down
docker-compose up -d
```

If you'd like to be able to log in to the record transfer app, you can create a superuser with these commands:

```shell
docker-compose exec app sh
python3 manage.py createsuperuser
```
