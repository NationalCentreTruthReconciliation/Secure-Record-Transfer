#
# Builder image
#
FROM node:20 AS builder

WORKDIR /build/

COPY package*.json .

# Create binary for minifying assets
RUN npm install && npm run compile


#
# Main image
#
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Copy files to container
COPY pyproject.toml README.md ./docker/entrypoint.sh /app/
COPY ./bagitobjecttransfer /app/bagitobjecttransfer

# Copy built binary from builder
COPY --from=builder /build/node_modules/yuglify/dist/* node_modules/yuglify/dist/

# Install Python dependencies
RUN pip install .

WORKDIR /app/bagitobjecttransfer/

ENTRYPOINT ["/app/entrypoint.sh"]
