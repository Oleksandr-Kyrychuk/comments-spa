#!/bin/bash
set -e  # вихід при будь-якій помилці

export PYTHONPATH=/app/comments_project:$PYTHONPATH

# --- PostgreSQL ---
echo "Waiting for PostgreSQL..."
export PGPASSWORD="${POSTGRES_PASSWORD:-user_password}"  # бери з env або дефолт
counter=0
max_attempts=30
until pg_isready -h "${POSTGRES_HOST:-postgres}" -U "${POSTGRES_USER:-user}" -d "${POSTGRES_DB:-comments_db}"; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
    counter=$((counter+1))
    if [ $counter -ge $max_attempts ]; then
        echo "PostgreSQL is still unavailable after $max_attempts attempts, exiting"
        exit 1
    fi
done
echo "PostgreSQL is ready!"

# --- Redis ---
if [ -z "$REDIS_URL" ]; then
    echo "REDIS_URL is not set. Exiting."
    exit 1
fi

# Витягуємо host, port і password з REDIS_URL
REDIS_HOST=$(echo "$REDIS_URL" | sed -E 's|redis://([^:]+):([^@]+)@([^:]+):([0-9]+)/.*|\3|')
REDIS_PORT=$(echo "$REDIS_URL" | sed -E 's|redis://([^:]+):([^@]+)@([^:]+):([0-9]+)/.*|\4|')
REDIS_PASSWORD=$(echo "$REDIS_URL" | sed -E 's|redis://([^:]+):([^@]+)@([^:]+):([0-9]+)/.*|\2|')

echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
counter=0
until redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" ping | grep -q PONG; do
    echo "Redis is unavailable - sleeping"
    sleep 2
    counter=$((counter+1))
    if [ $counter -ge $max_attempts ]; then
        echo "Redis is still unavailable after $max_attempts attempts, exiting"
        exit 1
    fi
done
echo "Redis is ready!"

# --- Запуск CMD (Django, Celery, etc) ---
exec "$@"
