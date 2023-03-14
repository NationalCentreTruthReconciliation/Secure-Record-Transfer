FROM python:3

# Set Work Directoy
WORKDIR /app

# Set Environment Variables
ENV PYTHONUNBUFFERED=1

# Make Directories
RUN mkdir -p /app/media/jobs/
RUN mkdir -p /var/log/django/
RUN mkdir -p /var/log/django-rq/

# Copy Project
COPY . .

# Install Dependencies
RUN apt update; \
    apt install -y netcat; \
    pip install --upgrade setuptools wheel; \
    pip install -r requirements.txt

# Prepare entrypoint script
RUN sed -i 's/\r$//g' /app/docker/entrypoint.sh; \
    chmod +x /app/docker/entrypoint.sh

ENTRYPOINT ["/app/docker/entrypoint.sh"]
