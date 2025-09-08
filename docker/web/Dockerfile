FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install additional packages
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    redis-tools

# Install GDAL binaries
RUN apt-get update && \
    apt-get install -y gdal-bin \
    libgdal-dev \
    libgeos-dev

# Clean up
RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Setup the python environment
COPY requirements/* requirements/
RUN pip install --upgrade pip && \
    pip install -r requirements/local.txt

# Install Node.js directly based on .nvmrc (nvm has shell dependency issues in Docker)
COPY .nvmrc .nvmrc
RUN NODE_VERSION=$(cat .nvmrc | tr -d 'v') && \
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    apt-get install -y nodejs

EXPOSE 8000
