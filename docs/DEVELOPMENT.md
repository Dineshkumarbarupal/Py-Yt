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

## Environment
For local Python execution, the database host is usually 127.0.0.1. In Docker Compose, the host is the service name mysql; compose sets that URL for the app container.

Uploads require MEDIA_BUCKET, MEDIA_ACCESS_KEY_ID and MEDIA_SECRET_ACCESS_KEY, and optionally MEDIA_ENDPOINT_URL and MEDIA_REGION. For Cloudflare R2, use the account-specific R2 S3 endpoint and region auto. For AWS, use an S3 bucket in the selected region. Configure bucket CORS to allow browser PUT uploads from the Py-Yt origin and the required content-type header. The upload URL is a short-lived signed PUT URL; the browser sends the raw file bytes, not multipart form fields. The backend verifies object ContentLength and ContentType after upload. A mismatch is rejected and the object is deleted where possible. Restrict storage credentials to the media bucket and required operations.

## Tests
Run pytest -q. The test suite uses a test database URL if DATABASE_URL is not supplied. CI runs against MySQL 8.4 and applies Alembic migrations before tests.

## Docker
1. Copy .env.example to .env.
2. Change all default secrets/passwords.
3. Run docker compose up --build.
4. Apply migrations: docker compose exec app alembic upgrade head.
5. Open http://localhost through Nginx.

Never use example credentials in an internet-accessible deployment.
