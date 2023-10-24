#!/bin/sh

# Wait for MySQL Database to be available if running in prod
if [ "$ENV" != 'dev' ]; then
  TESTPORTSCRIPT=$(cat <<END
import socket
is_open, sock = False, None
try:
    sock = socket.socket()
    sock.settimeout(30)
    sock.connect(('$MYSQL_HOST', $MYSQL_PORT))
except socket.error:
    is_open = False
else:
    is_open = True
finally:
    if sock is not None:
        sock.close()
print('OK' if is_open else 'KO')
END
)

  until [ "$(python -c "$TESTPORTSCRIPT")" = 'OK' ]
  do
    echo "Waiting for database connection..."
    # wait for 5 seconds before check again
    sleep 5
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
