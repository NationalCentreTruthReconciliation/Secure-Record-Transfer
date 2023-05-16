################################################################################
#
# BASE IMAGE
#
FROM python:3 as base

# Set Work Directoy
WORKDIR /app

# Set Environment Variables
ENV PYTHONUNBUFFERED=1

# Make Directories
RUN mkdir -p /app/media/jobs/
RUN mkdir -p /var/log/django/
RUN mkdir -p /var/log/django-rq/

# Copy app files
COPY . .

# Install Dependencies
RUN apt update; \
    apt install -y netcat; \
    pip install --upgrade setuptools wheel; \
    pip install -r requirements.txt

# Prepare entrypoint script
RUN sed -i 's/\r$//g' /app/docker/entrypoint.sh; \
    chmod +x /app/docker/entrypoint.sh


################################################################################
#
# DEVELOPMENT
#
FROM base as dev

ENTRYPOINT ["/app/docker/entrypoint.sh"]


################################################################################
#
# PRODUCTION
#
FROM base as prod

# Create user to run app as
RUN addgroup -S app && adduser -S app -G app

# Set ownership of everything to app:app
RUN chown -R app:app /app

USER app

ENTRYPOINT ["/app/docker/entrypoint.sh"]
