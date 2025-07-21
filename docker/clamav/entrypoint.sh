#!/bin/bash
set -e

# Set default if not provided
export MAX_SINGLE_UPLOAD_SIZE_MB="${MAX_SINGLE_UPLOAD_SIZE_MB:-64}"

echo "Generating ClamAV configuration from template..."
envsubst < /etc/clamav/clamd.conf.template > /etc/clamav/clamd.conf

# Execute the original entrypoint command
exec /init