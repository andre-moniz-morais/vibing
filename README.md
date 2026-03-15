# vibing

A modern project management platform built with Django, featuring real-time collaborative editing, Kanban boards, and AI-powered story workflows.

## Features

- **Workspaces & Projects** — Organize work with role-based access (Admin, Editor, Reader)
- **User Stories** — Create and manage stories with inline editing for titles, points, and assignees
- **Kanban Board** — Drag-and-drop task management across customizable columns
- **Real-time Editing** — Collaborative Editor.js-powered documentation with WebSocket sync
- **OAuth Login** — Sign in with GitHub or Google
- **S3 Support** — Optional cloud storage for uploaded images

## Tech Stack

- **Backend**: Django 6, Django REST Framework, Django Channels (WebSockets)
- **Frontend**: Django Templates, Vanilla JS, Editor.js
- **Async**: Daphne (ASGI), Celery, Redis
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Storage**: Local filesystem or AWS S3

## Local Setup

### Prerequisites

- Python 3.11+
- Redis (for WebSockets and Celery)

### 1. Clone the repository

```bash
git clone https://github.com/andre-moniz-morais/vibing.git
cd vibing
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

- **GitHub/Google OAuth**: Create OAuth apps and paste the client ID and secret
- **S3** (optional): Set `USE_S3=True` and fill in AWS credentials

### 5. Run database migrations

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Start Redis

```bash
redis-server
```

### 8. Start the development server

```bash
python manage.py runserver
```

The server starts with Daphne (ASGI) at `http://localhost:8000/`.

### 9. Start Celery worker (for AI tasks)

In a separate terminal:

```bash
celery -A vibing worker -l info
```

## Docker

### Build and run with Docker Compose

```bash
docker-compose up --build
```

This starts:
- **web** — Django app on port 8000
- **redis** — Redis on port 6379
- **celery** — Background worker

### Environment variables

Pass environment variables via `.env` file or Docker Compose `environment` section.

## Project Structure

```
vibing/
├── core/           # Models, API views, WebSocket consumers, Celery tasks
├── frontend/       # Django views, URL routing
├── templates/      # HTML templates (Django template engine)
├── static/         # CSS, JavaScript
├── vibing/         # Django project settings, ASGI config
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Roles

| Role   | Permissions                                           |
|--------|-------------------------------------------------------|
| Admin  | Full access, manage members, edit settings            |
| Editor | Create/edit stories, edit project info, drag Kanban    |
| Reader | View-only access to all content                       |
