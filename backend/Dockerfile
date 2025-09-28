FROM python:3.11-slim

WORKDIR /app

# Встановлення системних залежностей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    curl \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо файл з залежностями та встановлюємо Python-пакети
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install daphne

# Копіюємо весь код проєкту
COPY . .

# Створюємо директорію для статичних файлів
RUN mkdir -p /app/comments_project/static

# Виконуємо collectstatic тільки якщо це web-service (PORT існує)
ARG PORT
RUN if [ -n "$PORT" ]; then python comments_project/manage.py collectstatic --noinput; fi

# Створюємо непривілейованого користувача
RUN useradd -m -u 1000 appuser

# Додаємо права на виконання скриптів
RUN chmod +x /app/entrypoint-django.sh
RUN chmod +x /app/entrypoint-celery.sh

# Змінюємо власника файлів на непривілейованого користувача
RUN chown -R appuser:appuser /app

# Перемикаємося на непривілейованого користувача
USER appuser

ENTRYPOINT ["/app/entrypoint-django.sh"]