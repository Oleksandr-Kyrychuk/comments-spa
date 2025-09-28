#!/bin/bash

# Add PYTHONPATH for proper imports
export PYTHONPATH=/app/comments_project:$PYTHONPATH

echo "REDIS_URL=$REDIS_URL"
echo "DATABASE_URL=$DATABASE_URL"

# Initial delay for PostgreSQL initialization
echo "Waiting for PostgreSQL initialization..."
sleep 5

# Wait for PostgreSQL
counter=0
max_attempts=30
until pg_isready -h postgres -U user -d comments_db; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
    counter=$((counter+1))
    if [ $counter -ge $max_attempts ]; then
        echo "PostgreSQL is still unavailable after $max_attempts attempts, exiting"
        exit 1
    fi
done

# Check Redis
if [ -z "$REDIS_URL" ]; then
    echo "REDIS_URL is not set. Exiting."
    exit 1
fi

echo "Waiting for Redis at $REDIS_URL..."
counter=0
until timeout 3 redis-cli -u "$REDIS_URL" ping | grep -q PONG; do
    echo "Redis is unavailable - sleeping"
    sleep 2
    counter=$((counter+1))
    if [ $counter -ge $max_attempts ]; then
        echo "Redis is still unavailable after $max_attempts attempts, exiting"
        exit 1
    fi
done
echo "Redis ready!"

# Apply migrations (optional, but good for consistency if worker needs DB access)
echo "Applying Django migrations..."
python /app/comments_project/manage.py migrate --noinput

# Start Celery worker
# -A specifies the app (your project name)
# -l info for logging level
# --concurrency=4 (adjust based on your plan's CPU; start low to avoid OOM)
exec celery -A comments_project worker -l info --concurrency=4