#!/bin/bash
set -e

# Add PYTHONPATH for proper imports
export PYTHONPATH=/app/comments_project:$PYTHONPATH

echo "PORT=$PORT"
echo "REDIS_URL=$REDIS_URL"
echo "DATABASE_URL=$DATABASE_URL"

# --- Parse DATABASE_URL for pg_isready ---
if [ -n "$DATABASE_URL" ]; then
    # Extract host, port, user from DATABASE_URL
    DB_HOST=$(echo $DATABASE_URL | sed -E 's/postgresql:\/\/[^:]*:[^@]*@([^:\/]*).*/\1/')
    DB_PORT=$(echo $DATABASE_URL | sed -E 's/postgresql:\/\/[^:]*:[^@]*@[^:]*:([0-9]*).*/\1/' || echo "5432")
    DB_USER=$(echo $DATABASE_URL | sed -E 's/postgresql:\/\/([^:]*):[^@]*@.*/\1/')

    echo "Waiting for PostgreSQL at host: $DB_HOST, port: $DB_PORT..."
    counter=0
    max_attempts=30
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
        counter=$((counter+1))
        if [ $counter -ge $max_attempts ]; then
            echo "PostgreSQL still unavailable after $max_attempts attempts, exiting"
            exit 1
        fi
    done
    echo "PostgreSQL ready!"
else
    echo "DATABASE_URL is not set. Exiting."
    exit 1
fi

# --- Wait for Redis ---
if [ -n "$REDIS_URL" ]; then
    echo "Waiting for Redis at $REDIS_URL..."
    counter=0
    max_attempts=30
    until timeout 3 redis-cli -u "$REDIS_URL" ping | grep -q PONG; do
        echo "Redis is unavailable - sleeping"
        sleep 2
        counter=$((counter+1))
        if [ $counter -ge $max_attempts ]; then
            echo "Redis still unavailable after $max_attempts attempts, exiting"
            exit 1
        fi
    done
    echo "Redis ready!"
else
    echo "REDIS_URL is not set. Exiting."
    exit 1
fi

# --- Run migrations ---
echo "Applying Django migrations..."
python /app/comments_project/manage.py migrate --noinput

# --- Check deployment ---
echo "Running Django deployment checks..."
python /app/comments_project/manage.py check --deploy

# --- Start Daphne ---
echo "Starting Daphne..."
exec daphne -b [::] -p "$PORT" comments_project.asgi:application