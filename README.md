# Comments SPA

## Project Overview
Comments SPA is a single-page application for managing threaded comments with user identification, file uploads, and real-time updates. Built with Django (backend) and Vue.js (frontend), it uses PostgreSQL for data storage, Redis for caching and message brokering, Celery for asynchronous tasks, and Django Channels for WebSocket-based real-time comment updates. The application supports JWT authentication, CAPTCHA for spam protection, and validated file uploads (images and text files). This project fulfills the **Junior+** level requirements, incorporating Queue (Celery), Cache (Redis), Events (WebSocket/signals), and JWT authentication.

## Features
- **Threaded Comments**: Supports nested comments with no depth limit (frontend renders up to 5 levels for performance).
- **Form Fields**:
  - **User Name**: Alphanumeric, required (client-side HTML5 validation with `pattern="^[a-zA-Z0-9]+$"`).
  - **Email**: Valid email format, required (client-side `type="email"`).
  - **Home Page**: Valid URL, optional (client-side `type="url"`).
  - **CAPTCHA**: Image-based, alphanumeric, refreshable via `/captcha/refresh/`, required.
  - **Text**: Supports HTML tags `<a href title>`, `<code>`, `<i>`, `<strong>` with server-side XSS sanitization using `bleach`.
- **File Uploads**:
  - Images (JPG, GIF, PNG) resized to 320x240 pixels server-side using `PIL`.
  - Text files (TXT) up to 100KB.
  - Lightbox effect for image previews using `vue-easy-lightbox`.
- **Sorting**: By username, email, or date (ascending/descending, default: LIFO via `-created_at`).
- **Pagination**: 25 top-level comments per page.
- **Real-Time Updates**: New comments/replies pushed via WebSocket using Django Channels.
- **Security**:
  - **XSS**: HTML sanitized with `bleach` (allowed tags: `<a>`, `<code>`, `<i>`, `<strong>`).
  - **SQL Injection**: Prevented by Django ORM.
  - **CSRF**: Enabled for forms via `/csrf-cookie/`.
  - **File Validation**: Server-side checks for file formats and sizes.
  - **CAPTCHA**: Server-side validation using `django-simple-captcha`.
  - **JWT**: Optional authentication for API (currently `AllowAny` for comment creation).
- **Asynchronous Processing**: Comment creation handled by Celery tasks with Redis as the broker.
- **Caching**: Comment lists cached in Redis with a 15-minute TTL.
- **Docker**: Fully containerized with `docker-compose.yml` for Django, Celery, PostgreSQL, Redis, and Vue.js frontend.

## Technology Stack
- **Backend**:
  - Django 4.x with Django REST Framework
  - Django Channels for WebSocket
  - Celery for asynchronous tasks
  - Redis for caching and message brokering
  - PostgreSQL for data storage
  - `bleach` for HTML sanitization
  - `django-simple-captcha` for CAPTCHA
  - `djangorestframework-simplejwt` for JWT authentication
- **Frontend**:
  - Vue.js 3 with Vuex for state management
  - Axios for API requests
  - `vue-easy-lightbox` for image previews
  - Tailwind CSS for styling
- **Deployment**:
  - Docker and `docker-compose.yml`
  - Nginx for serving frontend static files
  - Daphne for ASGI backend

## Database Schema
- **users**:
  - `id`: Auto-incrementing primary key
  - `username`: CharField, max 50, alphanumeric (RegexValidator `^[a-zA-Z0-9]+$`)
  - `email`: EmailField, required
  - `homepage`: URLField, optional
  - `created_at`: DateTimeField (auto_now_add)
  - Indexes: [username, email]
- **comments**:
  - `id`: Auto-incrementing primary key
  - `user`: ForeignKey to `users` (CASCADE)
  - `text`: TextField, max 5000 chars
  - `parent`: ForeignKey to self, optional (CASCADE)
  - `file`: FileField, optional (uploads to `uploads/%Y/%m/%d/`)
  - `created_at`: DateTimeField (auto_now_add)
  - Indexes: [created_at, user_id], [parent_id]
- Schema file: `docs/schema.sql` (exported for MySQL Workbench compatibility)

## Security
- **XSS**: HTML sanitized server-side with `bleach`.
- **SQL Injection**: Prevented by Django ORM.
- **CSRF**: Enabled for forms with CSRF token via `/csrf-cookie/`.
- **File Validation**: Images resized to 320x240, TXT files limited to 100KB, formats validated server-side.
- **CAPTCHA**: Alphanumeric, image-based, validated server-side.
- **JWT**: Configured for API authentication, though comment creation currently allows anonymous users.

## Known Issues and Improvements
- **Table View**: Top-level comments use `<div>` with indentation instead of a table for responsiveness. A table-based UI can be implemented if required.
- **XHTML Validation**: `bleach` sanitizes HTML but does not enforce strict XHTML tag closure. Can add `lxml` for full compliance.
- **JWT Enforcement**: Comment creation allows anonymous users for flexibility. Can restrict to authenticated users with `IsAuthenticated`.
- **Tests**: Minimal tests in `tests.py`. Additional functional tests for comment creation, file uploads, and API endpoints recommended.
- **Client-Side Validation**: Limited to HTML5 attributes. JavaScript validation for HTML tags and file checks can be added.

## Installation and Setup
### Prerequisites
- Docker and Docker Compose
- Node.js 18 (for local frontend development)
- Python 3.11 (for local backend development)

### Local Development with Docker
1. Clone the repository:
   ```bash
   git clone <https://github.com/Oleksandr-Kyrychuk/comments-spa/>
   cd comments-spa
   ```
2. Copy environment files:
   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env
   ```
3. Update `.env` files with appropriate values (e.g., `SECRET_KEY`, `VUE_APP_API_URL`).
4. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```
5. Access the application:
   - Frontend: `http://localhost:8080`
   - Backend API: `http://localhost:8000/api`
   - Admin panel: `http://localhost:8000/admin` (create superuser with 'cd backend/comments_project' and  `python manage.py createsuperuser`)

### Local Development without Docker
1. Backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python comments_project/manage.py migrate
   python comments_project/manage.py runserver
   ```
2. Frontend:
   ```bash
   cd frontend
   npm install
   npm run serve
   ```

### Deployment
- **Hosting**: Tested on Railway.com.
- **Steps**:
  1. Set environment variables (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`) in the hosting platform.
  2. Push Docker images to a registry (e.g., Docker Hub).
  3. Deploy using `Dockers` or platform-specific configuration (e.g., Render blueprint).
  4. Ensure `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` include the hosting domain.

## API Endpoints
- **GET /api/comments/**: List top-level comments (paginated, sortable).
- **POST /api/comments/**: Create a comment (with optional file and parent).
- **POST /preview/**: Preview sanitized comment text.
- **GET/POST /captcha/**: Generate CAPTCHA.
- **GET /captcha/refresh/**: Refresh CAPTCHA.
- **POST /api/token/**: Obtain JWT token.
- **POST /api/token/refresh/**: Refresh JWT token.
- **GET /csrf-cookie/**: Get CSRF token.
- **WebSocket /ws/comments/**: Real-time comment updates.

## Video Demonstration
[Link to video](https://your-video-hosting-service.com/video) (upload and update link before submission).

