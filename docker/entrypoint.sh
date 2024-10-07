#!/bin/sh

if [ "$ENV" != 'dev' ]; then
  # Wait for MySQL Database to be available if running in prod
  until python manage.py wait_for_db --max-retries 10 --retry-interval 5
  do
    echo "** Trying again **"
  done

  # Each of these tasks should only be run once
  if [ "$IS_RQ" = 'yes' ]; then
    echo ">> Running database migrations."
    python manage.py migrate --no-input
  else
    echo ">> Collecting static files."
    python manage.py collectstatic --no-input
  fi
fi

echo ">> Starting app."
exec "$@"
