#!/bin/bash

# Додаємо PYTHONPATH для забезпечення правильного імпорту
export PYTHONPATH=/app/comments_project:$PYTHONPATH

echo "PORT=$PORT"
echo "REDIS_URL=$REDIS_URL"
echo "DATABASE_URL=$DATABASE_URL"

# Початкова затримка для ініціалізації PostgreSQL
echo "Waiting for PostgreSQL initialization..."
sleep 5

# Чекаємо PostgreSQL
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

# Перевірка Redis
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

# Міграції
echo "Applying Django migrations..."
python /app/comments_project/manage.py migrate --noinput

# Перевірка $PORT
if [ -z "$PORT" ]; then
    echo "PORT is not set by Railway. Exiting."
    exit 1
fi

# Запуск Daphne
pip install gunicorn  # Додай в requirements.txt якщо немає
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 comments_project.wsgi:application
