# BagIt Transfer Portal

Please, [read the docs!](https://nctr-bagit-record-transfer.readthedocs.io/en/latest/)

This is a file transfer application made for securely transferring files over the internet and securing them in a BagIt bag for archivists to view. The CAAIS is observed in this application, and a large portion of the metadata fields specified in that document are present in this application's transfer form.

## Quickstart

To start the record transfer application, ensure you have [Docker Desktop](https://www.docker.com/products/docker-desktop) or some version of `docker-compose` installed on your system. You will also need Python 3 installed on your system.

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
