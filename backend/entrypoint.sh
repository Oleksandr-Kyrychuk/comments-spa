#!/bin/sh

# Чекаємо, поки база даних стане доступною
echo "Waiting for database..."
sleep 5

# Чекаємо, поки Redis стане доступним
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  echo "Redis is unavailable - sleeping"
  sleep 1
done

# Робимо міграції
echo "Applying Django migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Запускаємо Daphne
echo "Starting Daphne server..."
exec daphne -b 0.0.0.0 -p 8000 comments_project.asgi:application
