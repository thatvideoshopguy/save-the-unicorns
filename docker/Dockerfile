# Use Ubuntu as base for both Node and Python
FROM ubuntu:22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    NODE_VERSION=20

# Install software-properties-common to manage repositories
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update


# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.13 \
    python3.13-dev \
    python3-pip \
    python3.13-venv \
    gcc \
    g++ \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set LD_LIBRARY_PATH to include the directory with GDAL libraries
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y nodejs

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser

# Set work directory and change ownership
WORKDIR /app
RUN chown appuser:appuser /app

# Switch to non-root user
USER appuser

# Create Python virtual environment and upgrade pip
RUN python3.13 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN pip install --upgrade pip

# Copy and install Python dependencies
COPY --chown=appuser:appuser requirements /app/requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy package files and install Node dependencies
COPY --chown=appuser:appuser package*.json /app/
RUN npm ci

# Copy frontend source files
COPY --chown=appuser:appuser webpack.config.js /app/
COPY --chown=appuser:appuser postcss.config.js /app/
COPY --chown=appuser:appuser static /app/static/

# Build frontend assets
RUN npm run production

# Copy application files
COPY --chown=appuser:appuser manage.py /app/
COPY --chown=appuser:appuser project /app/project/
COPY --chown=appuser:appuser apps /app/apps/
COPY --chown=appuser:appuser templates /app/templates/
COPY --chown=appuser:appuser gunicorn.conf.py /app/
COPY --chown=appuser:appuser docker/healthcheck.py /app/

# Make the entrypoint script executable
COPY --chown=appuser:appuser docker/docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Create static and media directories
RUN mkdir -p /app/htdocs/static /app/htdocs/media

# Collect static files
RUN python manage.py collectstatic --noinput --settings=project.settings.production

# Clean up Node modules to reduce image size (optional)
RUN rm -rf node_modules



# Expose port
EXPOSE 8000

# Set entrypoint and default command
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "project.wsgi:application"]
