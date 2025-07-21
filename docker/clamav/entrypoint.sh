#!/bin/bash
set -e

# Generate the actual config from template using environment variables
echo "Generating ClamAV configuration from template..."
envsubst < /etc/clamav/clamd.conf.template > /etc/clamav/clamd.conf

if [ $# -eq 0 ]; then
  exec /init
else
  exec "$@"
fi