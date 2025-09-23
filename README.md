# Comments SPA

## Project Overview
Comments SPA is a single-page application for managing threaded comments with user identification, file uploads, and real-time updates. The project is built using Django (backend) and Vue.js (frontend), with PostgreSQL for data storage, Redis for caching and message brokering, Celery for asynchronous tasks, and WebSocket (Django Channels) for real-time comment updates. It supports user authentication via JWT, CAPTCHA for spam protection, and file uploads (images and text files) with validation.

This project meets the requirements for a **Junior+** level, implementing Queue (Celery), Cache (Redis), Events (WebSocket), and JWT authentication.

## Features
- **Threaded Comments**: Supports nested (cascade) comments with no depth limit (frontend renders up to 5 levels).
- **Form Fields**:
  - **User Name**: Alphanumeric (required).
  - **Email**: Valid email format (required).
  - **Home Page**: Valid URL (optional).
  - **CAPTCHA**: Image-based, alphanumeric, refreshable (required).
  - **Text**: Supports HTML tags `<a href title>`, `<code>`, `<i>`, `<strong>` with XSS sanitization.
- **File Uploads**:
  - Images (JPG, GIF, PNG) resized to 320x240 pixels.
  - Text files (TXT) up to 100KB.
  - Lightbox effect for image preview (via vue-easy-lightbox).
- **Sorting**: By username, email, or date (ascending/descending, default: LIFO).
- **Pagination**: 25 comments per page for top-level comments.
- **Real-Time Updates**: New comments are pushed via WebSocket.
- **Security**:
  - XSS protection via `bleach` (sanitizes HTML tags).
  - SQL injection protection via Django ORM.
  - CSRF protection for forms.
  - Optional JWT authentication for comment creation.
- **Asynchronous Processing**: Comment creation via Celery tasks.
- **Caching**: Comment list cached in Redis (15-minute TTL).
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
- Node.js 18 (for local frontend development, optional).
- Python 3.11 (for local backend development, optional).

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
- This starts Django (port 8000), Celery, Redis, PostgreSQL, and Nginx (port 8080).
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
   - Use the tag buttons ([i], [strong], [code], [a]) to insert allowed HTML.
   - Optionally upload an image (JPG/GIF/PNG) or TXT file.
   - Click "Preview" to see sanitized text.
   - Submit to post (processed asynchronously via Celery, pushed via WebSocket).
3. **View Comments**:
   - Comments are displayed in a threaded view with pagination (25 per page).
   - Sort by username, email, or date using the dropdown.
   - Click images to view in a lightbox.
4. **Reply**: Click "Reply" to add nested comments.
5. **JWT Authentication** (optional):
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
The schema is designed for PostgreSQL and can be visualized in MySQL Workbench (export via `pg_dump` or Workbench-compatible tools).
- **users**:
  - id (PK)
  - username (varchar, alphanumeric, required)
  - email (varchar, email format, required)
  - homepage (varchar, URL, optional)
  - created_at (datetime)
  - Indexes: [username, email]
- **comments**:
  - id (PK)
  - user (FK to users, on_delete=CASCADE)
  - text (text, max 5000 chars, sanitized HTML)
  - parent (FK to self, nullable, on_delete=CASCADE)
  - file (file, uploads/YYYY/MM/DD/, nullable)
  - created_at (datetime)
  - Indexes: [created_at, user], [parent]

## Security
- **XSS**: HTML sanitized with `bleach` (allowed: `<a>`, `<code>`, `<i>`, `<strong>`).
- **SQL Injection**: Prevented by Django ORM.
- **CSRF**: Enabled for forms, CSRF token via `/csrf-cookie/`.
- **File Validation**: Images resized to 320x240, TXT <=100KB, formats checked.
- **CAPTCHA**: Alphanumeric, image-based, validated server-side.
- **JWT**: Optional authentication for API (IsAuthenticatedOrReadOnly).

## Known Issues and Improvements
- **Table View**: Frontend uses div-based threads instead of a table for top-level comments (TBD: add table UI).
- **XHTML Validation**: `bleach` sanitizes tags but does not enforce strict XHTML tag closure (TBD: add lxml check).
- **JWT Enforcement**: Comment creation allows anonymous users (TBD: enforce IsAuthenticated for user tracking).
- **Tests**: Basic test file exists, but no functional tests (TBD: add tests for Comment creation).

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
- To generate schema for MySQL Workbench:
  ```bash
  docker-compose exec postgres pg_dump -h postgres -U user -d comments_db --schema-only > schema.sql
  ```
- Video demonstration available (TBD: include link to uploaded video).

## Contact
For feedback or issues, contact the developer at [your-email@example.com].