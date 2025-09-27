#!/bin/bash

# Додаємо PYTHONPATH для забезпечення правильного імпорту
export PYTHONPATH=/app/comments_project:$PYTHONPATH

# Початкова затримка для ініціалізації PostgreSQL
echo "Waiting for PostgreSQL initialization..."
sleep 5

# Чекаємо, поки PostgreSQL буде доступним (максимум 30 спроб)
echo "Waiting for PostgreSQL..."
export PGPASSWORD=user_password
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

# Чекаємо, поки Redis буде доступним (максимум 30 спроб)
echo "Waiting for Redis..."
counter=0
until redis-cli -h redis ping | grep -q PONG; do
    echo "Redis is unavailable - sleeping"
    sleep 2
    counter=$((counter+1))
    if [ $counter -ge $max_attempts ]; then
        echo "Redis is still unavailable after $max_attempts attempts, exiting"
        exit 1
    fi
done

# Виконуємо міграції
echo "Applying Django migrations..."
python /app/comments_project/manage.py migrate --noinput

# Додаємо перевірку доступності сервера
echo "Starting Daphne server..."
# Запускаємо Daphne у передньому плані
exec "$@"