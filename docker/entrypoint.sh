#!/bin/sh

if [ "$ENV" != 'dev' ]; then
  # Wait for MySQL Database to be available if running in prod
  until python manage.py wait_for_db --max-retries 10 --retry-interval 5
  do
    echo "** Trying again **"
  done
fi

# Run database migrations in RQ container
if [ "$IS_RQ" = 'yes' ]; then
  echo ">> Running database migrations."
  python manage.py migrate --no-input
  echo ">> Starting RQ worker(s)"

# Bundle, minify, and collect static assets in the Django container
else
  echo ">> Running webpack to bundle + minify assets."
  npm run build
  echo ">> Collecting static files."
  python manage.py collectstatic --no-input --clear --ignore recordtransfer/**/*.js --ignore recordtransfer/**/*.css
  echo ">> Starting app"

fi

exec "$@"
