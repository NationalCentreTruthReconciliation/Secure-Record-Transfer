#!/bin/sh

if [ "$ENV" != 'dev' ]; then
  # Wait for MySQL Database to be available if running in prod
  until python manage.py wait_for_db --max-retries 10 --retry-interval 5
  do
    echo "** Trying again **"
  done
fi

# Run database migrations in RQ container
if [ "$SERVICE_NAME" = 'rq' ]; then
  echo ">> Running database migrations."
  python manage.py migrate --no-input
  echo ">> Verifying settings."
  python manage.py verify_settings

  # This runs in the containerfile for production. This is included here for
  # dev because the locale/ directory is in the app/ folder, which gets shared
  # as a volume locally with the container; this means the compiled messages
  # would get overwritten when the volume is shared.
  if [ "$ENV" = 'dev' ]; then
    echo ">> Compiling messages."
    python manage.py compilemessages --ignore .venv
  fi

  echo ">> Starting RQ worker(s)"

elif [ "$SERVICE_NAME" = 'rq-scheduler' ]; then
  echo ">> Starting RQ scheduler"

elif [ "$SERVICE_NAME" = 'app' ]; then
  if [ "$ENV" != 'dev' ]; then
    echo ">> Fixing volume permissions."
    sudo chown -R myuser:myuser /opt/secure-record-transfer/app/static/
    sudo chown -R myuser:myuser /opt/secure-record-transfer/app/media/
    echo "OK"

    echo ">> Collecting static files."
    python manage.py collectstatic --no-input --clear \
      --ignore "recordtransfer/**/*.js" \
      --ignore "recordtransfer/**/*.ts"
  fi

  echo ">> Starting app"

fi

exec "$@"
