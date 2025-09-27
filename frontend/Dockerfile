# -------------------------------
# Етап 1: Збірка Vue.js
# -------------------------------
FROM node:18 AS build

# Робоча директорія всередині контейнера
WORKDIR /app

# Копіюємо package.json та package-lock.json і встановлюємо залежності
COPY package*.json ./
RUN npm install

# Копіюємо весь проект і збираємо Vue
COPY . .
RUN npm run build

# -------------------------------
# Етап 2: Nginx для статичних файлів
# -------------------------------
FROM nginx:alpine

# Копіюємо зібрані статичні файли з попереднього етапу
COPY --from=build /app/dist /usr/share/nginx/html

# Копіюємо власний конфіг Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Відкриваємо порт 80
EXPOSE 80

# Запускаємо Nginx у foreground
CMD ["nginx", "-g", "daemon off;"]
