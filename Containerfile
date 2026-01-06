FROM docker.io/python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1
ENV PROJ_DIR="/opt/secure-record-transfer/"
ENV APP_DIR="/opt/secure-record-transfer/app/"
ENV NVM_VERSION=0.40.3
ENV NODE_VERSION=24.12.0
ENV PNPM_VERSION=10.27.0

WORKDIR ${PROJ_DIR}

# 🔧 Install curl for downloading files, gettext for for internationalization and libmagic for MIME type detection
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gettext \
    libmagic1 && \
    rm -rf /var/lib/apt/lists/*

# Install nvm (Node Version Manager) and install NodeJS
# This does not activate nvm for use in the container. To do that, you need to run ". /nvm/nvm.sh"
ENV NVM_DIR="/nvm"
RUN mkdir "${NVM_DIR}" && \
    curl -o- "https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh" | bash && \
    . "$NVM_DIR/nvm.sh" && \
    nvm install "${NODE_VERSION}" && \
    nvm alias default "v${NODE_VERSION}" && \
    nvm use default
ENV PATH="$NVM_DIR/versions/node/v${NODE_VERSION}/bin/:$PATH"

# Install uv and install Python dependencies
# Uses a persistent cache mount for uv (see https://docs.astral.sh/uv/guides/integration/docker/#caching)
COPY --from=ghcr.io/astral-sh/uv:0.8.8 /uv /uvx /bin/
ENV UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ${PROJ_DIR}
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

# Install pnpm and install Javascript dependencies
# Uses a persistent cache mount for pnpm (see https://pnpm.io/docker#minimizing-docker-image-size-and-build-time)
RUN npm install -g "pnpm@${PNPM_VERSION}"
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ${PROJ_DIR}
RUN --mount=type=cache,id=pnpm,target=/root/.cache/pnpm \
    pnpm install --frozen-lockfile --prod

# Copy application code to image
COPY ./app ${APP_DIR}

# Make arg passed from compose files into environment variable
ARG WEBPACK_MODE=production
ENV WEBPACK_MODE=${WEBPACK_MODE}

# Run webpack to bundle and minify assets
COPY webpack.config.mjs postcss.config.mjs tsconfig.json ${PROJ_DIR}
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
# TEST IMAGE
#

FROM dev AS test

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --extra dev

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


FROM docker.io/python:3.11-slim AS prod

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
