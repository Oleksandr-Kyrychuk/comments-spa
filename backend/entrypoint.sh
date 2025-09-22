#!/bin/sh

# Чекаємо, поки база даних стане доступною (можна замінити на wait-for-it)
echo "Waiting for database..."
sleep 5

# Робимо міграції
echo "Applying Django migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Запускаємо Daphne
echo "Starting Daphne server..."
exec daphne -b 0.0.0.0 -p 8000 comments_project.asgi:application
