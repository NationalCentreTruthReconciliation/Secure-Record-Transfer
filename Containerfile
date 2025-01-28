FROM nikolaik/python-nodejs:python3.10-nodejs22-slim AS builder

ENV PYTHONUNBUFFERED=1

# Make arg passed from compose files into environment variable
ARG WEBPACK_MODE
ENV WEBPACK_MODE $WEBPACK_MODE

WORKDIR /app/

# Install build dependencies and poetry
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
    && \
    curl -sSL https://install.python-poetry.org | python3 - --version 1.8.5

# Copy poetry-related files, and install Python dependencies
COPY pyproject.toml poetry.lock README.md /app/
RUN poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true && \
    poetry install -E prod

# Copy Node-related files, and install NodeJS dependencies
COPY package*.json webpack.config.js /app/
RUN npm install --no-color

# Copy application code to image
COPY ./bagitobjecttransfer /app/bagitobjecttransfer

# Run webpack to bundle and minify assets
RUN npm run build


FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

RUN apt-get update && \
    apt-get install -y --no-install-recommends default-mysql-client && \
    rm -rf /var/lib/apt/lists/*

# Copy built assets from builder image
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/bagitobjecttransfer /app/bagitobjecttransfer

# Activate virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Copy entrypoint script to image
COPY ./docker/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

WORKDIR /app/bagitobjecttransfer/

ENTRYPOINT ["/app/entrypoint.sh"]
