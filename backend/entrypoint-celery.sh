#!/bin/bash
set -e

# Add PYTHONPATH for proper imports
export PYTHONPATH=/app/comments_project:$PYTHONPATH

echo "DATABASE_URL=$DATABASE_URL"
echo "REDIS_URL=$REDIS_URL"

# --- Wait for PostgreSQL (via DATABASE_URL) ---
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for PostgreSQL at $DATABASE_URL..."
    until pg_isready -d "$DATABASE_URL" >/dev/null 2>&1; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "PostgreSQL ready!"
else
    echo "DATABASE_URL is not set. Exiting."
    exit 1
fi

# --- Wait for Redis (only if REDIS_URL is set) ---
if [ -n "$REDIS_URL" ]; then
    echo "Waiting for Redis at $REDIS_URL..."
    until redis-cli -u "$REDIS_URL" ping | grep -q PONG; do
        echo "Redis is unavailable - sleeping"
        sleep 2
    done
    echo "Redis ready!"
else
    echo "No REDIS_URL set. Skipping Redis check."
fi

# --- Run migrations (optional, but keeps schema up to date) ---
echo "Applying Django migrations..."
python /app/comments_project/manage.py migrate --noinput

# --- Start Celery worker ---
echo "Starting Celery worker..."
exec celery -A comments_project worker -l info --concurrency=4
