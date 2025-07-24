#!/usr/bin/env sh
set -e

# Ensure the application data directory exists and is writable
mkdir -p /app/data
chmod 0777 /app/data

# Always run all pending Django migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create or update the admin user
echo "Creating or updating admin user..."
python manage.py create_admin

# Collect all static assets
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Hand off control to the main application process
exec "$@"
