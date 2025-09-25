# Comments SPA

## Project Overview
Comments SPA is a single-page application for managing threaded comments with user identification, file uploads, and real-time updates. Built with Django (backend) and Vue.js (frontend), it uses PostgreSQL for data storage, Redis for caching and message brokering, Celery for asynchronous tasks, and Django Channels for WebSocket-based real-time comment updates. The application supports JWT authentication, CAPTCHA for spam protection, and validated file uploads (images and text files).

This project fulfills the **Junior+** level requirements, incorporating Queue (Celery), Cache (Redis), Events (WebSocket), and JWT authentication.

## Features
- **Threaded Comments**: Supports nested comments with no depth limit (frontend renders up to 5 levels for performance).
- **Form Fields**:
  - **User Name**: Alphanumeric, required.
  - **Email**: Valid email format, required.
  - **Home Page**: Valid URL, optional.
  - **CAPTCHA**: Image-based, alphanumeric, refreshable, required.
  - **Text**: Supports HTML tags `<a href title>`, `<code>`, `<i>`, `<strong>` with XSS sanitization.
- **File Uploads**:
  - Images (JPG, GIF, PNG) resized to 320x240 pixels.
  - Text files (TXT) up to 100KB.
  - Lightbox effect for image previews using vue-easy-lightbox.
- **Sorting**: By username, email, or date (ascending/descending, default: LIFO).
- **Pagination**: 25 comments per page for top-level comments.
- **Real-Time Updates**: New comments are pushed via WebSocket.
- **Security**:
  - XSS protection via `bleach` for HTML sanitization.
  - SQL injection prevention via Django ORM.
  - CSRF protection for forms.
  - Optional JWT authentication for comment creation.
- **Asynchronous Processing**: Comment creation handled by Celery tasks.
- **Caching**: Comment lists cached in Redis with a 15-minute TTL.
- **Docker**: Fully containerized with Django, Celery, Redis, PostgreSQL, and Nginx.

## Tech Stack
- **Backend**: Django 4.2, Django REST Framework, Django Channels, Celery, django-redis, rest_framework_simplejwt, django-captcha.
- **Frontend**: Vue.js 3, Vuex, vue-easy-lightbox, axios.
- **Database**: PostgreSQL 15.
- **Cache/Queue**: Redis 7.2.
- **Containerization**: Docker, Docker Compose.
- **Web Server**: Nginx (frontend), Daphne (Django ASGI).

## Project Structure
```
comments-spa/
├── docs/
│   └── schema.sql
├── backend/
│   ├── comments/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── consumers.py
│   │   ├── models.py
│   │   ├── routing.py
│   │   ├── serializers.py
│   │   ├── signals.py
│   │   ├── tasks.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── comments_project/
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── db/
│   │   └── init.sql (optional, for test data)
│   ├── Dockerfile
│   ├── entrypoint-celery.sh
│   ├── entrypoint-django.sh
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CommentForm.vue
│   │   │   ├── CommentItem.vue
│   │   │   ├── CommentList.vue
│   │   │   └── HelloWorld.vue
│   │   ├── store/
│   │   │   ├── comments.js
│   │   │   └── index.js
│   ├── Dockerfile
│   ├── package.json
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```

## Prerequisites
- Docker and Docker Compose installed.
- Git for cloning the repository.
- Node.js 18 (optional, for local frontend development).
- Python 3.11 (optional, for local backend development).

## Installation and Setup
### 1. Clone the Repository
```bash
git clone <repository-url>
cd comments-spa
```

### 2. Set Up Environment Variables
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:user_password@postgres:5432/comments_db
REDIS_URL=redis://redis:6379/0
```

### 3. Build and Run with Docker
```bash
docker-compose up --build
```
- Starts Django (port 8000), Celery, Redis, PostgreSQL, and Nginx (port 8080).
- Django migrations are applied automatically via `entrypoint-django.sh`.
- Access the app at `http://localhost:8080`.

### 4. Create a Superuser (Optional)
```bash
docker-compose exec django python /app/comments_project/manage.py createsuperuser
```
Access the admin panel at `http://localhost:8000/admin/`.

### 5. Testing
Run tests (basic setup, expand as needed):
```bash
docker-compose exec django python /app/comments_project/manage.py test
```

## Usage
1. **Open the App**: Navigate to `http://localhost:8080`.
2. **Create a Comment**:
   - Fill in the form (username, email, optional homepage, text, CAPTCHA).
   - Use tag buttons ([i], [strong], [code], [a]) to insert allowed HTML.
   - Optionally upload an image (JPG/GIF/PNG) or TXT file.
   - Click "Preview" to see sanitized text.
   - Submit to post (processed asynchronously via Celery, pushed via WebSocket).
3. **View Comments**:
   - Comments are displayed in a threaded view with pagination (25 per page).
   - Sort by username, email, or date using the dropdown.
   - Click images to view in a lightbox.
4. **Reply**: Click "Reply" to add nested comments.
5. **JWT Authentication** (Optional):
   - Get a token: `POST /api/token/` with `{ "username": "", "password": "" }`.
   - Include `Authorization: Bearer <token>` in API requests.

## API Endpoints
- **GET /api/comments/**: List top-level comments (paginated, 25 per page).
  - Query params: `ordering=user__username,user__email,created_at,-created_at`, `page=<number>`.
- **POST /api/comments/**: Create a comment (multipart/form-data).
  - Body: `{ "user": { "username": "", "email": "", "homepage": "" }, "text": "", "parent": null|<id>, "file": <file>, "captcha_0": "", "captcha_1": "" }`.
  - Returns 202 Accepted, processes via Celery.
- **POST /api/preview/**: Preview sanitized text.
  - Body: `{ "text": "" }`.
- **GET /csrf-cookie/**: Get CSRF token for form submissions.
- **GET /captcha/refresh/**: Refresh CAPTCHA image.
- **POST /api/token/**: Obtain JWT token.
- **POST /api/token/refresh/**: Refresh JWT token.

## WebSocket
- Connect to `ws://localhost:8000/ws/comments/` for real-time comment updates.
- Events: `new_comment` with serialized comment data.

## Database Schema
The database schema is defined in `docs/schema.sql` for PostgreSQL and can be visualized in MySQL Workbench for review as per the test assignment requirements. This file contains the SQL code to create the `users` and `comments` tables with appropriate constraints and indexes.

To apply the schema manually in a PostgreSQL environment:
```bash
psql -U user -d postgres -f docs/schema.sql
```

To generate the schema from the running PostgreSQL instance (alternative method):
```bash
docker-compose exec postgres pg_dump -h postgres -U user -d comments_db --schema-only > docs/schema.sql
```

- **users**:
  - id (PK, BIGSERIAL)
  - username (VARCHAR(50), alphanumeric, required)
  - email (VARCHAR(255), email format, required)
  - homepage (VARCHAR(255), URL, optional)
  - created_at (TIMESTAMP WITH TIME ZONE)
  - Indexes: [username, email]
- **comments**:
  - id (PK, BIGSERIAL)
  - user_id (FK to users, ON DELETE CASCADE)
  - text (TEXT, max 5000 chars, sanitized HTML)
  - parent_id (FK to self, nullable, ON DELETE CASCADE)
  - file (VARCHAR(255), uploads/YYYY/MM/DD/, nullable)
  - created_at (TIMESTAMP WITH TIME ZONE)
  - Indexes: [created_at, user_id], [parent_id]

## Security
- **XSS**: HTML sanitized with `bleach` (allowed: `<a>`, `<code>`, `<i>`, `<strong>`).
- **SQL Injection**: Prevented by Django ORM.
- **CSRF**: Enabled for forms, CSRF token via `/csrf-cookie/`.
- **File Validation**: Images resized to 320x240, TXT <=100KB, formats checked.
- **CAPTCHA**: Alphanumeric, image-based, validated server-side.
- **JWT**: Optional authentication for API (IsAuthenticatedOrReadOnly).

## Known Issues and Improvements
- **Table View**: Top-level comments use div-based threads instead of a table for better responsiveness and mobile compatibility. A table-based UI can be added if required.
- **XHTML Validation**: `bleach` sanitizes HTML but does not enforce strict XHTML tag closure. A check via `lxml` can be added for full compliance.
- **JWT Enforcement**: Comment creation allows anonymous users for flexibility. Can be restricted to authenticated users if needed.
- **Tests**: Basic tests exist in `tests.py`. Functional tests for comment creation and API endpoints can be added for robustness.

## Deployment
- **Hosting**: Tested on Render.com. Set `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY` in environment variables.
- **Steps**:
  1. Push Docker images to a registry (e.g., Docker Hub).
  2. Deploy with `docker-compose.yml` or Render blueprint.
  3. Ensure `ALLOWED_HOSTS` includes the hosting domain.

## Development Notes
- For local development without Docker:
  ```bash
  cd backend
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py runserver
  cd ../frontend
  npm install
  npm run serve
  ```
- Video demonstration: [Link to video](https://your-video-hosting-service.com/video) (TBD: upload and update link).

## Contact
For feedback or issues, contact the developer at [your-email@example.com].