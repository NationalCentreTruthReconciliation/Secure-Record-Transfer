# Secure Record Transfer Application

Please, [read the docs!](https://secure-record-transfer.readthedocs.io/en/latest/)

The secure record transfer application has been designed for the purpose of transferring files and metadata over the internet to an institution before securing the files in a [BagIt](https://datatracker.ietf.org/doc/html/rfc8493) bag. This application attempts to closely follow the [Canadian Archival Accession Information Standard (CAAIS)](http://archivescanada.ca/CWG_AccessionStandard). As such, most of the fields in the Accession Standard are captured when a user submits files and metadata through the application's [transfer form](https://nctr-bagit-record-transfer.readthedocs.io/en/latest/howtouse/transferform.html). A suite of administrative tools is also provided with the app to allow staff members to view, appraise, download, an export submissions made by users.

## AtoM Compatibility

This application is compatible with version 2.x of [AtoM](https://www.accesstomemory.org/en/), an open-source archival access database. Administrators can export an accession CSV from the application's backend, and directly import those CSVs into AtoM to create accession records. **Note** that some fields are dropped in the conversion of CAAIS to AtoM-compliant Accession records, as certain fields in the Accession Standard are not present in the AtoM accession module. This issue is actively being addressed.

## Quickstart

This application is run using Docker or Podman. Ensure you have [Docker Desktop](https://www.docker.com/products/docker-desktop) or [Podman Desktop](https://podman-desktop.io/) installed on your system before running the app. If you want to use Podman, you will also need [Podman Compose](https://github.com/containers/podman-compose).

From a terminal, clone the repository:

```shell
git clone https://github.com/NationalCentreTruthReconciliation/Secure-Record-Transfer.git
```

Enter the `Secure-Record-Transfer/bagitobjecttransfer` directory:

```shell
cd Secure-Record-Transfer/bagitobjecttransfer
```

Make a copy of the example `.dev.env` file and run the application:

```shell
cp example.dev.env .dev.env

# If using docker:
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# If using podman + podman compose:
podman-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

After the containers are built, the application should now be accessible at http://localhost:8000. Any emails that are sent by the application are intercepted by the mail application running at http://localhost:8025.

Run these commands to build the database after the app starts in Docker.

```shell
# If using docker:
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec app python manage.py migrate --no-input

# If using podman + podman compose:
podman-compose -f docker-compose.yml -f docker-compose.dev.yml exec app python manage.py migrate --no-input
```

To restart the application, run these commands.

```shell
# If using docker:
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# If using podman + podman compose:
podman-compose -f docker-compose.yml -f docker-compose.dev.yml down
podman-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

If you'd like to be able to log in to the record transfer app as an administrator, use the following command, and follow the prompts you are given.

```shell
# If using docker:
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec app python manage.py createsuperuser

# If using podman + podman compose:
podman-compose -f docker-compose.yml -f docker-compose.dev.yml exec app python manage.py createsuperuser
```
