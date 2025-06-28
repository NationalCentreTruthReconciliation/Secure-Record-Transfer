FROM nikolaik/python-nodejs:python3.10-nodejs22-slim AS base

ENV PYTHONUNBUFFERED=1
ENV PROJ_DIR="/opt/secure-record-transfer/"
ENV APP_DIR="/opt/secure-record-transfer/app/"

WORKDIR ${PROJ_DIR}

# 🔧 Install gettext for makemessages (includes msguniq)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gettext && \
    rm -rf /var/lib/apt/lists/*

# Copy uv-related files, and install Python dependencies
COPY pyproject.toml uv.lock ${PROJ_DIR}
RUN uv sync

# Install Node.js dependencies
COPY package*.json ${PROJ_DIR}
RUN npm install --no-color

# Copy application code to image
COPY ./app ${APP_DIR}

# Make arg passed from compose files into environment variable
ARG WEBPACK_MODE
ENV WEBPACK_MODE ${WEBPACK_MODE}

# Run webpack to bundle and minify assets
COPY webpack.config.js postcss.config.mjs ${PROJ_DIR}
RUN npm run build

# Copy entrypoint script to image
COPY ./docker/entrypoint.sh ${PROJ_DIR}
RUN chmod +x ${PROJ_DIR}/entrypoint.sh



################################################################################
#
# DEVELOPMENT IMAGE
#

FROM base as dev

ENV PYTHONUNBUFFERED=1

# Activate virtual environment
ENV PATH="${PROJ_DIR}/.venv/bin:${PATH}"
ENV VIRTUAL_ENV="${PROJ_DIR}/.venv"

WORKDIR ${APP_DIR}

ENTRYPOINT ["/opt/secure-record-transfer/entrypoint.sh"]

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
RUN uv sync --extra prod


FROM python:3.10-slim AS prod

ENV PYTHONUNBUFFERED=1
ENV PROJ_DIR="/opt/secure-record-transfer/"
ENV APP_DIR="/opt/secure-record-transfer/app/"

# Create non-root user with same UID for consistency
RUN useradd --create-home --uid 1000 myuser && \
    mkdir -p ${APP_DIR} && \
    chown -R myuser:myuser ${PROJ_DIR}


# Install required dependencies for mysqlclient and curl for health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends default-mysql-client curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder ${PROJ_DIR}/entrypoint.sh ${PROJ_DIR}/entrypoint.sh
COPY --from=builder ${PROJ_DIR}/.venv ${PROJ_DIR}/.venv
COPY --from=builder ${PROJ_DIR}/dist ${PROJ_DIR}/dist
COPY --from=builder ${APP_DIR} ${APP_DIR}

# Set ownership AFTER copying files
RUN chown -R myuser:myuser ${PROJ_DIR}

# Activate virtual environment
ENV PATH="${PROJ_DIR}/.venv/bin:$PATH"
ENV VIRTUAL_ENV="${PROJ_DIR}/.venv"

WORKDIR ${APP_DIR}
USER myuser

ENTRYPOINT ["/opt/secure-record-transfer/entrypoint.sh"]
