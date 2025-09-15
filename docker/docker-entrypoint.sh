#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
python manage.py wait_for_db --settings=project.settings.production --timeout 30

# Run migrations
echo "Running migrations..."
python manage.py migrate --settings=project.settings.production

# Create superuser if it doesn't exist
 python manage.py createsuperuser --noinput --settings=project.settings.production || true

# Setup Wagtail data
echo "Setting up Wagtail data..."
python manage.py setup_wagtail --settings=project.settings.production

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=project.settings.production

echo "Starting application..."
exec "$@"
