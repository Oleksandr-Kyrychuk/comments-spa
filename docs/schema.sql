-- Створення бази даних
CREATE DATABASE comments_db
    WITH ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

\connect comments_db;

-- Таблиця для користувачів
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    homepage VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_username CHECK (username ~ '^[a-zA-Z0-9]+$'),
    CONSTRAINT valid_email CHECK (email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
    UNIQUE (username, email)
);

-- Індекс для таблиці users
CREATE INDEX idx_username_email ON users (username, email);

-- Таблиця для коментарів
CREATE TABLE comments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    text TEXT NOT NULL,
    parent_id BIGINT,
    file VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_parent FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE,
    CONSTRAINT valid_text_length CHECK (LENGTH(text) <= 5000)
);

-- Індекси для таблиці comments
CREATE INDEX idx_created_at_user ON comments (created_at, user_id);
CREATE INDEX idx_parent ON comments (parent_id);

-- Коментарі до структури бази даних
COMMENT ON TABLE users IS 'Таблиця для зберігання інформації про користувачів (username, email, homepage)';
COMMENT ON TABLE comments IS 'Таблиця для зберігання коментарів із підтримкою каскадного відображення (parent_id)';
COMMENT ON COLUMN comments.text IS 'Текст коментаря з дозволеними HTML-тегами (<a>, <code>, <i>, <strong>)';
COMMENT ON COLUMN comments.file IS 'Шлях до файлу (зображення JPG/GIF/PNG <= 320x240 або TXT <= 100KB)';