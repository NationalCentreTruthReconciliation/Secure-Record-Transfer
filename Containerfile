FROM nikolaik/python-nodejs:python3.10-nodejs22-slim

ENV PYTHONUNBUFFERED=1

# Install poetry
RUN python -m pip install --user pipx && \
    python -m pipx ensurepath && \
    python -m pipx install poetry

WORKDIR /app/

# Copy Node-related files, and install NodeJS dependencies
COPY package*.json webpack.config.js /app/
# Copy script files
COPY ./scripts /app/scripts

RUN npm install --no-color

# Copy poetry-related files, and install Python dependencies
COPY pyproject.toml poetry.lock README.md /app/
RUN poetry config virtualenvs.create false && poetry install

# Copy application code to image
COPY ./docker/entrypoint.sh /app/
COPY ./bagitobjecttransfer /app/bagitobjecttransfer

WORKDIR /app/bagitobjecttransfer/

ENTRYPOINT ["/app/entrypoint.sh"]
