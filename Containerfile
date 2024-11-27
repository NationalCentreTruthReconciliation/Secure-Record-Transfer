#
# Builder image
#
FROM docker.io/denoland/deno:alpine-2.1.1 AS builder

WORKDIR /build/

COPY deno.json deno.lock /build/

# Create binary for minifying assets
RUN deno install && deno compile --no-check -A npm:yuglify


#
# Main image
#
FROM docker.io/python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Copy built binary from builder
COPY --from=builder /build/yuglify* /app/
RUN chmod +x /app/yuglify*

# Copy files to container
COPY pyproject.toml README.md ./docker/entrypoint.sh /app/
COPY ./bagitobjecttransfer /app/bagitobjecttransfer

# Install Python dependencies
RUN pip install .

WORKDIR /app/bagitobjecttransfer/

ENTRYPOINT ["/app/entrypoint.sh"]
