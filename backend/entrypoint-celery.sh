#!/bin/bash
set -e

# Вказуємо Python шлях і settings
export PYTHONPATH=/app/comments_project:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=comments_project.settings

# --- PostgreSQL ---
echo "Waiting for PostgreSQL..."
export PGPASSWORD="${POSTGRES_PASSWORD:-user_password}"
counter=0
max_attempts=30

until pg_isready -h "${POSTGRES_HOST:-postgres}" -U "${POSTGRES_USER:-user}" -d "${POSTGRES_DB:-comments_db}"; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
    counter=$((counter+1))
    if [ $counter -ge $max_attempts ]; then
        echo "PostgreSQL still unavailable after $max_attempts attempts"
        exit 1
    fi
done
echo "PostgreSQL ready!"

# --- Redis ---
if [ -z "$REDIS_URL" ]; then
    echo "REDIS_URL is not set. Exiting."
    exit 1
fi

echo "Waiting for Redis at $REDIS_URL..."
counter=0
until redis-cli -u "$REDIS_URL" ping | grep -q PONG; do
    echo "Redis is unavailable - sleeping"
    sleep 2
    counter=$((counter+1))
    if [ $counter -ge $max_attempts ]; then
        echo "Redis still unavailable after $max_attempts attempts"
        exit 1
    fi
done
echo "Redis ready!"

# --- Запуск CMD (Celery / Django / інше) ---
exec "$@"
