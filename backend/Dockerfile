FROM python:3.11-slim

WORKDIR /app/comments_project
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Встановлюємо Daphne для ASGI (WebSocket)
RUN pip install daphne

# Команда для запуску (Daphne для ASGI, Gunicorn для HTTP)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "comments_project.asgi:application"]
