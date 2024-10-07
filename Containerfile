#
# Builder image
#
FROM docker.io/node:20 AS builder

WORKDIR /build/

COPY package*.json /build/

# Create binary for minifying assets
RUN npm install && npm run compile


#
# Main image
#
FROM docker.io/python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Copy built binary from builder
COPY --from=builder /build/node_modules/yuglify/dist/* /app/node_modules/yuglify/dist/

# Copy files to container
COPY pyproject.toml README.md ./docker/entrypoint.sh /app/
COPY ./bagitobjecttransfer /app/bagitobjecttransfer

# Install Python dependencies
RUN pip install .

WORKDIR /app/bagitobjecttransfer/

ENTRYPOINT ["/app/entrypoint.sh"]
