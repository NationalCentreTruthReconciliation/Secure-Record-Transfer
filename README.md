# Secure Record Transfer Application

Please, [read the docs!](https://secure-record-transfer.readthedocs.io/en/latest/)

The secure record transfer application has been designed for the purpose of transferring files and standardized metadata over the internet to an institution. This application attempts to closely follow the [Canadian Archival Accession Information Standard (CAAIS)](https://archivescanada.ca/wp-content/uploads/2023/07/CAAIS_2019May15_EN.pdf). As such, most of the fields in the Accession Standard are captured when a user submits files and metadata through the application's [transfer form](https://nctr-bagit-record-transfer.readthedocs.io/en/latest/howtouse/transferform.html). A suite of administrative tools is also provided with the app to allow staff members to view, appraise, download, an export submissions made by users. Submissions can be downloaded by administrators in the [BagIt](https://datatracker.ietf.org/doc/html/rfc8493) format.

## AtoM Compatibility

This application is compatible with version 2.x of [AtoM](https://www.accesstomemory.org/en/), an open-source archival access database. Administrators can export an accession CSV from the application's backend, and directly import those CSVs into AtoM to create accession records. **Note** that some fields are dropped in the conversion of CAAIS to AtoM-compliant Accession records, as certain fields in the Accession Standard are not present in the AtoM accession module. This issue is actively being addressed.

## Quickstart

This application is run using Podman or Docker. If you are using Podman, ensure you have these packages installed on your system:

- [Podman Desktop](https://podman-desktop.io/)
- [Python](https://python.org)
- [Podman Compose](https://github.com/containers/podman-compose)

If you would prefer to use Docker, ensure you have [Docker Desktop](https://www.docker.com/products/docker-desktop) installed on your system.

To start, clone the repository:

```shell
git clone https://github.com/NationalCentreTruthReconciliation/Secure-Record-Transfer.git
```
(Optional) From the root of the repository, make a copy of the development environment variable file.

```shell
cp example.dev.env .dev.env
```

You can view the various settings which can be configured and defined in `.dev.env` [here](https://secure-record-transfer.readthedocs.io/en/latest/settings/index.html).

**For the following commands, substitute `docker compose` for `podman-compose` if you're using Docker instead of Podman.**

To start up the application, run the following command:

```shell
podman-compose -f compose.dev.yml up -d
```

The database will not be populated at first. To migrate the database, run this command:

```shell
podman-compose -f compose.dev.yml exec app python manage.py migrate
```

After the containers are built and running, the application should now be accessible at http://localhost:8000. Any emails that are sent by the application are intercepted by the mail application running at http://localhost:8025. For example, if you sign up using the sign-up form, you can find those at http://localhost:8025.

To restart the application, run these commands:

```shell
podman-compose -f compose.dev.yml down
podman-compose -f compose.dev.yml up -d
```

If you'd like to be able to log in to the record transfer app as an administrator, use the following command, and follow the prompts you are given.

```shell
podman-compose -f compose.dev.yml exec app python manage.py createsuperuser
```

## Developers

See the [DEVELOPERS.md](DEVELOPERS.md) file for more info on setting your development environment up to work on this application.
