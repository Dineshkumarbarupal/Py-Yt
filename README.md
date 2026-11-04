# Py-Yt — Video Platform

Py-Yt is an independent, modular video-sharing and creator platform inspired by the broad product experience of YouTube.

## Status
The repository was initially empty. This commit initializes the project documentation and establishes the intended direction. Features are not considered complete until implemented and tested.

## Product direction
- Viewer experience: discovery, search, watch pages, Shorts-style vertical videos, subscriptions, playlists, history, watch later, likes, comments, captions and accessibility.
- Creator experience: channel management, uploads, video metadata, processing status, live-stream setup, comments moderation, analytics and monetization readiness.
- Platform experience: authentication, profiles, notifications, reporting, safety controls, admin moderation, settings and auditability.
- Advanced discovery: configurable feeds and recommendation pipelines with transparent controls.
- AI-assisted workflows: optional creator assistance and content discovery, subject to explicit user consent and provider constraints.

## Technology
- Frontend: HTML5, CSS3, vanilla JavaScript ES modules
- Backend: Python + FastAPI
- Persistence: MySQL + SQLAlchemy + Alembic
- Background processing: Redis + worker queue (introduced when required)
- Media: object storage + transcoding pipeline + HLS/DASH delivery (provider selected for deployment)
- Deployment: Docker, Nginx, CI pipeline

## Important platform boundary
Py-Yt is an independent product, not a copy of YouTube's proprietary backend. YouTube content and account actions will only be integrated through permitted official APIs, OAuth scopes, embeddable players, and documented platform capabilities. API quota, eligibility, region, copyright, privacy, and monetization restrictions apply. Py-Yt will not bypass YouTube access controls, scrape private account data, or impersonate YouTube.

## Development phases
1. Foundation and usable MVP
2. Advanced architecture and scale preparation
3. Enterprise architecture
4. Multi-region/global scale architecture

Capacity targets are planning goals and require load testing before any performance claim.

## Local setup
See `docs/DEVELOPMENT.md` for the planned local workflow. A complete runnable release will require environment configuration, MySQL, migrations, media storage credentials, tests and security review.

## Deployment
See `docs/DEPLOYMENT.md`. Railway is the suggested first deployment target for an early MVP; DigitalOcean App Platform or a managed VPS/Kubernetes setup may be more suitable as operational requirements grow.

## Project status
This repository is at initialization stage. Do not treat the feature roadmap as a statement that those features are already implemented.
