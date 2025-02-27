#!/bin/sh

# Wait for MySQL Database to be available if running in prod
until python manage.py wait_for_db --max-retries 10 --retry-interval 5
do
  echo "** Trying again **"
done

# Run database migrations in RQ container
if [ "$IS_RQ" = 'yes' ]; then
  echo ">> Running database migrations."
  python manage.py migrate --no-input
  echo ">> Starting RQ worker(s)"

else
  if [ "$ENV" != 'dev' ]; then
    echo ">> Collecting static files."
    python manage.py collectstatic --no-input --clear \
      --ignore "recordtransfer/**/*.js" \
      --ignore "recordtransfer/**/*.css" \
      --ignore "recordtransfer/**/*.jpg" \
      --ignore "recordtransfer/**/*.jpeg" \
      --ignore "recordtransfer/**/*.png" \
      --ignore "recordtransfer/**/*.webp"
  fi

  echo ">> Starting app"

fi

exec "$@"
