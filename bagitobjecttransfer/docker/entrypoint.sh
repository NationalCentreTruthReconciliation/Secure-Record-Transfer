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
fi

exec "$@"
