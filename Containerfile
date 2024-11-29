#
# Main image
#
FROM docker.io/python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Copy files to container
COPY pyproject.toml README.md ./docker/entrypoint.sh /app/
COPY ./bagitobjecttransfer /app/bagitobjecttransfer

# # Install Python dependencies
# RUN pip install .

# Install Node.js
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean

COPY package*.json webpack.config.js /app/

RUN npm install && npm run build

# ENTRYPOINT ["/app/entrypoint.sh"]
