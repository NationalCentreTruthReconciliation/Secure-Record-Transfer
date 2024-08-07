FROM python:3.10

WORKDIR /tmp

# Install NodeJS
RUN apt-get update \
    && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh \
    && bash nodesource_setup.sh \
    && apt-get install -y nodejs \
    && npm install -g npm \
    && npm install

# Set Environment Variables
ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Copy files to container
COPY pyproject.toml package.json package-lock.json README.md ./docker/entrypoint.sh ./bagitobjecttransfer/ /app/

# Install Python dependencies
RUN pip install .

WORKDIR /app/bagitobjecttransfer/

ENTRYPOINT ["/app/entrypoint.sh"]
