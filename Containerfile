FROM nikolaik/python-nodejs:python3.11-nodejs22-slim AS base

ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV PROJ_DIR="/opt/secure-record-transfer/"
ENV APP_DIR="/opt/secure-record-transfer/app/"
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

WORKDIR ${PROJ_DIR}

# 🔧 Install gettext for for internationalization and libmagic for MIME type detection
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gettext \
    libmagic1 && \
    rm -rf /var/lib/apt/lists/*

# Install pnpm globally
RUN npm install -g pnpm@latest-10

# Copy uv-related files, and install Python dependencies
# Uses a persistent cache mount for uv (see https://docs.astral.sh/uv/guides/integration/docker/#caching)
COPY pyproject.toml uv.lock ${PROJ_DIR}
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

# Install Node.js dependencies with pnpm
# Uses a persistent cache mount for pnpm (see https://pnpm.io/docker#minimizing-docker-image-size-and-build-time)
COPY package.json pnpm-lock.yaml ${PROJ_DIR}
RUN --mount=type=cache,id=pnpm,target=${PNPM_HOME}/store \
    pnpm install --frozen-lockfile --prod

# Copy application code to image
COPY ./app ${APP_DIR}

# Make arg passed from compose files into environment variable
ARG WEBPACK_MODE=production
ENV WEBPACK_MODE ${WEBPACK_MODE}

# Run webpack to bundle and minify assets
COPY webpack.config.js postcss.config.mjs ${PROJ_DIR}
RUN pnpm run build

# Copy entrypoint script to image
COPY ./docker/entrypoint.sh ${PROJ_DIR}
RUN chmod +x ${PROJ_DIR}/entrypoint.sh



################################################################################
#
# DEVELOPMENT IMAGE
#

FROM base AS dev

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

ENV UV_LINK_MODE=copy
ENV APP_DIR="/opt/secure-record-transfer/app/"

# Install build tools for production dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    gettext

# Install production dependencies (e.g., mysqlclient)
# Compile byte code to improve startup time (see https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --extra prod --compile-bytecode

# Compile locale message files
RUN uv run python "${APP_DIR}/manage.py" compilemessages --ignore .venv


FROM python:3.11-slim AS prod

ENV PYTHONUNBUFFERED=1
ENV PROJ_DIR="/opt/secure-record-transfer/"
ENV APP_DIR="/opt/secure-record-transfer/app/"

# Create non-root user with same UID for consistency
RUN useradd --create-home --uid 1000 myuser && \
    mkdir -p ${APP_DIR} && \
    chown -R myuser:myuser ${PROJ_DIR}

# Install required dependencies for mysqlclient and curl for health checks
# Allow myuser to fix permissions on static and media volumes with sudo
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-mysql-client \
    curl \
    sudo \
    libmagic1 && \
    rm -rf /var/lib/apt/lists/* && \
    echo "myuser ALL=(ALL) NOPASSWD: /usr/bin/chown -R myuser\\:myuser /opt/secure-record-transfer/app/static/" >> /etc/sudoers && \
    echo "myuser ALL=(ALL) NOPASSWD: /usr/bin/chown -R myuser\\:myuser /opt/secure-record-transfer/app/media/" >> /etc/sudoers

COPY --from=builder --chown=myuser:myuser ${PROJ_DIR}/entrypoint.sh ${PROJ_DIR}/entrypoint.sh
COPY --from=builder --chown=myuser:myuser ${PROJ_DIR}/.venv ${PROJ_DIR}/.venv
COPY --from=builder --chown=myuser:myuser ${PROJ_DIR}/dist ${PROJ_DIR}/dist
COPY --from=builder --chown=myuser:myuser ${APP_DIR} ${APP_DIR}

# Activate virtual environment
ENV PATH="${PROJ_DIR}/.venv/bin:$PATH"
ENV VIRTUAL_ENV="${PROJ_DIR}/.venv"

WORKDIR ${APP_DIR}
USER myuser

ENTRYPOINT ["/opt/secure-record-transfer/entrypoint.sh"]
