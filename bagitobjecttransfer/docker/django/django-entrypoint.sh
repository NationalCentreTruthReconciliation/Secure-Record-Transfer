#!/bin/bash

echo "Creating job directory"
mkdir -p /app/media/jobs

echo "Collecting static files..."
python3 manage.py collectstatic --clear --no-input -v0 --settings=bagitobjecttransfer.settings.docker

echo "Running Django app"
python3 manage.py runserver 0.0.0.0:8000 --settings=bagitobjecttransfer.settings.docker
