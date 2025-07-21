# This is a custom image for Debian-based ClamAV, but with gettext installed
# to allow for environment variable substitution in configuration files.

FROM docker.io/clamav/clamav-debian

# Install gettext for envsubst
RUN apt-get update && apt-get install -y gettext && rm -rf /var/lib/apt/lists/*