FROM python:3.11-slim

WORKDIR /app/comments_project

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install daphne

COPY . .

# Додаємо права на запуск entrypoint
RUN chmod +x /app/comments_project/entrypoint.sh

# Використовуємо entrypoint для запуску міграцій та сервера
CMD ["/app/comments_project/entrypoint.sh"]
