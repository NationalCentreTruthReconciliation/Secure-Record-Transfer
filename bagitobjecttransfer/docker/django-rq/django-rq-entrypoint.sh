#!/bin/bash

echo "Creating migrations..."
python3 manage.py makemigrations --no-input --settings=bagitobjecttransfer.settings.docker

echo "Applying migrations..."
python3 manage.py migrate --no-input --settings=bagitobjecttransfer.settings.docker

echo "Running Django RQ worker"
python3 manage.py rqworker default --settings=bagitobjecttransfer.settings.docker
