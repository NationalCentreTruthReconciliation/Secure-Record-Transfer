FROM python:3.10-slim

WORKDIR /tmp

COPY package*.json .

# Install NodeJS
RUN python -c "from urllib.request import urlretrieve; urlretrieve('https://deb.nodesource.com/setup_22.x', 'nodesource_setup.sh')" \
    && bash nodesource_setup.sh \
    && apt-get install -y nodejs \
    && npm install -g npm \
    && npm install \
    && rm nodesource_setup.sh

# Set Environment Variables
ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Copy files to container
COPY pyproject.toml README.md ./docker/entrypoint.sh ./bagitobjecttransfer/ /app/

# Install Python dependencies
RUN pip install --upgrade pip wheel setuptools \
    && pip install .

WORKDIR /app/bagitobjecttransfer/

ENTRYPOINT ["/app/entrypoint.sh"]
