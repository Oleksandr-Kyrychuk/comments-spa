FROM python:3.11-slim

WORKDIR /app

# Встановлення залежностей для MySQL, PostgreSQL, redis-cli та curl
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    postgresql-client \
    redis-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Встановлення залежностей Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install daphne
RUN python manage.py collectstatic --noinput

COPY . .

# Створюємо непрівільованого користувача
RUN useradd -m -u 1000 appuser

# Додаємо права на запуск entrypoint
RUN chmod +x /app/entrypoint-django.sh
RUN chmod +x /app/entrypoint-celery.sh

# Змінюємо власника файлів
RUN chown -R appuser:appuser /app

# Перемикаємося на непрівільованого користувача
USER appuser



# Додаємо ENTRYPOINT та CMD
ENTRYPOINT ["/app/entrypoint-django.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "comments_project.asgi:application"]