# Py-Yt — Modular Video Platform

Py-Yt is an independent video-sharing and creator platform inspired by YouTube's product categories. It is not a clone of YouTube's proprietary backend, algorithms, private catalog or licensed services.

## Current repository status

The original repository was empty. A modular FastAPI/MySQL web foundation has now been committed to the main branch. The files represent an implementation scaffold; the project has not yet completed runtime, integration, security or deployment verification.

### Implemented in code
- Modular FastAPI application and versioned REST API.
- HTML templates, reusable components, responsive CSS and ES-module JavaScript.
- MySQL SQLAlchemy models and Alembic migrations for users, channels, videos, playlists, subscriptions, reactions, comments and watch history.
- Registration/login/logout/current-user APIs with Argon2 password hashing and cookie-based JWT sessions; profile, avatar and password settings with current-password verification.
- Channel profile APIs, public video catalog/search/feed and category filtering.
- Playlist creation/list/detail, channel subscriptions and a latest-from-subscriptions feed, comments, reactions, Watch Later, history, watch progress and in-app notifications.
- Creator Studio overview, creator-owned content list, basic video analytics and comment hide/restore workflows.
- In-app notifications for new public uploads, new subscribers, comments and comment replies, with unread counters and mark-read actions.
- Presigned direct-to-S3-compatible video upload, object metadata verification and expiring signed playback URLs.
- Dockerfile, Docker Compose, Nginx configuration and GitHub Actions CI workflow.
- Architecture, feature roadmap, API, security, development and deployment documentation.

### Not yet implemented or verified
Shorts feed, video transcoding/HLS renditions, live streaming/chat, recommendations, advanced player controls, caption pipeline, retention/traffic-source analytics, custom thumbnails, full moderation/admin, notification delivery, monetization, MFA/recovery and enterprise/global infrastructure are roadmap items. A feature is not complete just because its route or UI placeholder exists.

## Technology
- Frontend: HTML5, CSS3, vanilla JavaScript ES modules
- Backend: Python + FastAPI
- Database: MySQL + SQLAlchemy + Alembic
- Media: S3-compatible object storage (Cloudflare R2 or AWS S3); signed upload/playback URLs
- Deployment: Docker, Nginx, CI; Redis/workers planned for later phases

## Repository layout

The project follows modular directories: asset, component, core, css, data, db, js, services, template, api, middleware, config, migrations, tests and docs.

## Run locally

1. Install Python 3.12+ and MySQL 8.4+.
2. Create and activate a virtual environment.
3. Install: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and set unique secrets and a valid MySQL URL.
5. Apply migrations: `alembic upgrade head`.
6. Run: `uvicorn main:app --reload`.
7. Visit `http://127.0.0.1:8000`; API docs are at `/docs` in non-production.

See [Development](docs/DEVELOPMENT.md), [Architecture](docs/ARCHITECTURE.md), [API index](docs/API.md), [Security](docs/SECURITY.md), [Feature roadmap](docs/FEATURE-ROADMAP.md) and [Deployment](docs/DEPLOYMENT.md).

## Deployment recommendation

Railway is recommended for the first MVP deployment, with Railway MySQL and a separate Cloudflare R2/AWS S3 media bucket. DigitalOcean App Platform plus Managed MySQL is a managed alternative. Review current pricing, region availability, storage egress and database backup options before provisioning.

## YouTube integration boundary

YouTube Data API/OAuth and the IFrame Player API are separate integration adapters. They are subject to official API methods, OAuth scopes, quota limits, user consent, region and platform policies. They do not grant a right or technical capability to download arbitrary YouTube videos, bypass DRM/ads or reproduce every YouTube account feature. Py-Yt's own user uploads and data are stored in its own database and media storage.

## Development phases

1. Phase 1 — Foundation/MVP
2. Phase 2 — Advanced architecture, Redis, background media workers and live workflows
3. Phase 3 — Enterprise governance, observability, HA and justified service extraction
4. Phase 4 — Global multi-region delivery and disaster recovery

User/hour capacity numbers are targets only. Do not claim capacity without workload definition and repeatable load tests.
