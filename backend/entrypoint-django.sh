#!/bin/bash
export PYTHONPATH=/app/comments_project:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=comments_project.settings
echo "PORT=$PORT"
echo "REDIS_URL=$REDIS_URL"
echo "DATABASE_URL=$DATABASE_URL"

echo "Waiting for PostgreSQL initialization..."
sleep 5

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
echo "PostgreSQL ready!"

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

echo "Applying Django migrations..."
python /app/comments_project/manage.py migrate --noinput
echo "Migrations applied!"

echo "Starting Celery worker..."
export DATABASE_URL=$DATABASE_URL
celery -A comments_project worker -l debug --concurrency 1 > celery.log 2>&1 &
echo "Celery worker started in background, logs in celery.log"

if [ -z "$PORT" ]; then
    echo "PORT is not set by Railway. Exiting."
    exit 1
fi

echo "Starting Daphne server..."
exec daphne -b [::] -p $PORT comments_project.asgi:application --verbosity 2