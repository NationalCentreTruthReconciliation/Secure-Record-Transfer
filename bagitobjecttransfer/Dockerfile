FROM python:3

# Set Work Directoy
WORKDIR /app

# Set Environment Variables
ENV PYTHONUNBUFFERED=1

# Copy app files
COPY . .

# Make directories, install dependencies and prepare entrypoint script
RUN mkdir -p /var/log/django/ \
    && mkdir -p /var/log/django-rq/ \
    && mkdir -p /app/static/ \
    && mkdir -p /app/media/ \
    && pip install --upgrade setuptools wheel \
    && pip install -r requirements.txt \
    && sed -i 's/\r$//g' /app/docker/entrypoint.sh \
    && chmod +x /app/docker/entrypoint.sh

ENTRYPOINT ["/app/docker/entrypoint.sh"]
