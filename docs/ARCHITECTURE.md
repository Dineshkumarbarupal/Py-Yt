# Py-Yt Architecture

## Phase 1: modular monolith

Py-Yt starts as a modular monolith. A single FastAPI deployment exposes versioned REST APIs, but code is separated by domain. This avoids premature microservices while keeping extraction boundaries clear.

### Application structure

- `main.py`: FastAPI construction, middleware, health route, static mounts and router registration.
- `webapp/pages.py`: server-rendered page routes and Jinja template rendering.
- `api/v1/endpoints/`: versioned REST endpoints grouped by domain.
- `services/`: reusable application services and cross-endpoint business operations.
- `db/` and `migrations/`: SQLAlchemy models/sessions/schemas and Alembic schema history.
- `core/`, `config/`, `middleware/`: security, storage adapters, settings, logging and request protection.
- `template/`, `component/`, `css/`, `js/`, `asset/`: viewer/creator UI, reusable templates, styles, ES modules and static assets.

## Domain modules
- Identity: users, credentials, sessions and account status.
- Channels: channel ownership, public profile and settings.
- Catalog: video metadata, visibility, lifecycle and category.
- Discovery: public feed and catalog search.
- Playback: permission checks and time-limited media URLs.
- Uploads: upload authorization, direct-to-storage transfer and object verification.
- Engagement: reactions, comments, subscriptions and watch progress.
- Collections: playlists and ordered playlist items.
- Creator Studio: content management, upload, later analytics and moderation.
- Trust & Safety: reports, moderation, policy actions and audit trails (planned).
- Live: stream scheduling, ingest, transcoding and chat (planned).

## Request and data flow

Browser HTML/CSS/ES modules -> HTTPS -> FastAPI /api/v1 routers -> Pydantic validation -> services/ use cases -> SQLAlchemy queries -> MySQL.

Video bytes bypass the API server: browser -> short-lived S3-compatible presigned PUT -> object storage. The API verifies uploaded-object size and MIME metadata after transfer. Playback uses short-lived signed GET URLs after checking video visibility and ownership.

## Data stores
- MySQL: users, channels, video metadata, playlists, subscriptions, comments, reactions and watch history.
- S3-compatible object storage: original videos and later renditions, thumbnails and captions.
- Redis: planned for caching, rate-limit counters and task queue in Phase 2.
- CDN: recommended for geographically distributed playback.

Do not store raw media blobs inside MySQL or on an ephemeral application container filesystem.

## Security boundaries
- Browser sessions are held in an HttpOnly expiring JWT cookie.
- A readable CSRF cookie is echoed through the X-CSRF-Token header for unsafe methods.
- Passwords use Argon2 hashing.
- Upload object keys are generated server-side.
- Private media is returned only after ownership checks, with expiring signed URLs.
- Secrets stay outside source control.

## Future extraction boundaries
Extract workers/services only when justified by measurements: media transcoding, notification delivery, search indexing, recommendation ranking, analytics aggregation, live ingest/chat and moderation. Keep MySQL as the initial relational source of truth.
