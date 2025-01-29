FROM nikolaik/python-nodejs:python3.10-nodejs22-slim AS base

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Install build dependencies and poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.8.5

# Copy poetry-related files, and install Python dependencies
COPY pyproject.toml poetry.lock README.md /app/
RUN poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true && \
    poetry install

# Install Node.js dependencies
COPY package*.json /app/
RUN npm install --no-color

# Copy application code to image
COPY ./bagitobjecttransfer /app/bagitobjecttransfer

# Make arg passed from compose files into environment variable
ARG WEBPACK_MODE
ENV WEBPACK_MODE $WEBPACK_MODE

# Run webpack to bundle and minify assets
COPY webpack.config.js /app/
RUN npm run build

# Copy entrypoint script to image
COPY ./docker/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

################################################################################
#
# DEVELOPMENT IMAGE
#

FROM base as dev

ENV PYTHONUNBUFFERED=1

# Activate virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

WORKDIR /app/bagitobjecttransfer/

ENTRYPOINT ["/app/entrypoint.sh"]

################################################################################
#
# PRODUCTION IMAGE
#

FROM base AS builder

# Install build tools for production dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config

# Install production dependencies (e.g., mysqlclient)
RUN poetry install -E prod


FROM python:3.10-slim AS prod

ENV PYTHONUNBUFFERED=1

# Install required dependencies for mysqlclient
RUN apt-get update && \
    apt-get install -y --no-install-recommends default-mysql-client && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/entrypoint.sh /app/entrypoint.sh
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/bagitobjecttransfer /app/bagitobjecttransfer

# Activate virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

WORKDIR /app/bagitobjecttransfer/

ENTRYPOINT ["/app/entrypoint.sh"]
