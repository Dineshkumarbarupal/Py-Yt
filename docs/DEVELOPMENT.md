# Local Development

## Requirements
- Python 3.12+
- MySQL 8.4+
- Git
- Optional: Docker Desktop
- S3-compatible bucket credentials for video uploads (Cloudflare R2 or AWS S3)

## Setup
1. Clone the repository and enter the project directory.
2. Create a virtual environment: python -m venv .venv.
3. Activate it and install dependencies: pip install -r requirements.txt.
4. Copy .env.example to .env.
5. Set a unique SECRET_KEY (32+ random characters), a local MySQL DATABASE_URL, and allowed CORS_ORIGINS.
6. Create a MySQL database named pyyt and a least-privilege user.
7. Apply schema migrations: alembic upgrade head.
8. Start the app: uvicorn main:app --reload.
9. Open http://127.0.0.1:8000; API docs are at /docs outside production.

## Repository structure

- `main.py` bootstraps the FastAPI app.
- `webapp/pages.py` owns HTML page routing.
- `api/v1/endpoints/` contains domain-specific REST routers.
- `services/` contains reusable application services.
- `db/` and `migrations/` contain the MySQL models and Alembic migration history.
- `template/`, `component/`, `css/` and `js/` contain the modular web UI.

For a Python syntax check run:
`python -m compileall -q main.py api core config db middleware migrations services scripts webapp`

## Environment
For local Python execution, the database host is usually 127.0.0.1. In Docker Compose, the host is the service name mysql; compose sets that URL for the app container.

Uploads require MEDIA_BUCKET, MEDIA_ACCESS_KEY_ID and MEDIA_SECRET_ACCESS_KEY, and optionally MEDIA_ENDPOINT_URL and MEDIA_REGION. For Cloudflare R2, use the account-specific R2 S3 endpoint and region auto. For AWS, use an S3 bucket in the selected region. Configure bucket CORS to allow browser PUT uploads from the Py-Yt origin and the required content-type header. The upload URL is a short-lived signed PUT URL; the browser sends the raw file bytes, not multipart form fields. The backend verifies object ContentLength and ContentType after upload. A mismatch is rejected and the object is deleted where possible. Restrict storage credentials to the media bucket and required operations.

## Tests
Run pytest -q. The test suite uses a test database URL if DATABASE_URL is not supplied. CI runs against MySQL 8.4 and applies Alembic migrations before tests.

## Docker Compose
1. Install Docker Desktop with WSL 2 integration on Windows, or Docker Engine + Compose plugin on Linux.
2. Copy .env.example to .env and replace every sample password and SECRET_KEY.
3. Set MEDIA_* values for an S3-compatible bucket if you need to upload videos.
4. Run docker compose up --build. Compose starts MySQL, waits for its healthcheck, runs Alembic in the one-shot migrate service, then starts FastAPI and Nginx.
5. Run docker compose ps and verify the mysql, migrate, app and nginx services are healthy/completed as expected.
6. Open http://localhost through Nginx.

For local use, APP_ENV=development allows the example DEBUG and local cookie settings. Do not carry those settings into production; production startup validates its required secrets, MySQL connection, secure cookies, allowed origin and object-storage credentials.

For schema changes, the migration service runs on the next compose up. To inspect logs use docker compose logs -f app migrate; to stop the stack use docker compose down. Persistent MySQL data remains in the named mysql_data volume.

Never use example credentials in an internet-accessible deployment.
