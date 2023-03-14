#!/bin/sh

# Wait for MySQL Database to be available
until nc -z -v -w30 $MYSQL_HOST $MYSQL_PORT
do
  echo "Waiting for database connection..."
  # wait for 5 seconds before check again
  sleep 5
done

exec "$@"
