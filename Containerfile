#
# Main image
#
FROM nikolaik/python-nodejs:python3.10-nodejs22-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Copy files to container
COPY pyproject.toml README.md ./docker/entrypoint.sh /app/
COPY ./bagitobjecttransfer /app/bagitobjecttransfer

# Install Python dependencies
RUN pip install .

COPY package*.json webpack.config.js /app/

RUN npm install

WORKDIR /app/bagitobjecttransfer/

ENTRYPOINT ["/app/entrypoint.sh"]
