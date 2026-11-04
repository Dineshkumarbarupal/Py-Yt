# Deployment Guide

## Recommended first host: Railway

For the current Phase 1 scope, Railway is the easiest initial target: it supports GitHub/Docker deployments and a MySQL service. The media bucket must be external object storage; do not use ephemeral app-disk storage for videos.

### Railway setup
1. Create a Railway project and connect your GitHub account.
2. Add a MySQL service.
3. Add a service from GitHub and select Dineshkumarbarupal/Py-Yt on branch main. Build using the root Dockerfile.
4. Set environment variables: APP_ENV=production, a newly generated SECRET_KEY, DATABASE_URL using the private MySQL service connection, CORS_ORIGINS for your production origin, SESSION_COOKIE_SECURE=true, and the MEDIA_* values for your S3/R2 bucket.
5. Set the pre-deploy command to: alembic upgrade head.
6. Set the healthcheck path to /health, generate a domain, then attach your custom domain and HTTPS.
7. Configure MySQL backups/point-in-time recovery where available and test restoring a backup.
8. Configure object-storage CORS to allow PUT from your production origin and the Content-Type request header. Do not store video bytes in the app container.
9. Verify health, login, upload, completion, publish, signed playback and database restore before public launch.

Railway documentation references:
- FastAPI: https://railway.com/guides/fastapi
- MySQL: https://docs.railway.com/databases/mysql
- Pre-deploy command: https://docs.railway.com/deployments/pre-deploy-command

## Alternative: DigitalOcean

DigitalOcean App Platform can deploy from Git repositories or container images. Pair it with Managed MySQL and object storage/CDN. It is a reasonable managed alternative when you prefer DigitalOcean's app and database controls. Confirm current region availability, plan limits and prices before provisioning.

Documentation: https://docs.digitalocean.com/products/app-platform/

## Advanced cloud option: Google Cloud

Cloud Run is a managed container platform for FastAPI. Pair it with Cloud SQL for MySQL, Cloud Storage for media, Cloud CDN and Secret Manager. It offers flexibility and scaling controls but requires more IAM, networking and billing configuration.

Documentation: https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-fastapi-service

## VPS / self-managed option

A Linux VPS with Docker Compose, MySQL, Nginx, object storage and monitoring provides more control and can be cost-efficient. You are responsible for OS updates, firewall, TLS, database backups, monitoring, incident response and recovery drills. It is not the simplest first deployment.

## Media delivery is separate from app hosting

Video encoding, storage and CDN egress can cost more than FastAPI compute. Use S3/R2 for original uploads, an FFmpeg worker pipeline for renditions (Phase 2), and a CDN for playback. Do not stream large video files through FastAPI workers.

## Production checklist
- Migrations run as a controlled pre-deploy/release job.
- App and database use private networking where supported.
- No sample or default secrets remain.
- HTTPS and secure cookies are active.
- CSRF, CORS and security headers are verified.
- Storage credentials are bucket-scoped and rotated.
- MySQL backups and restoration are tested.
- Object-store lifecycle/retention policies are defined.
- Logs, errors, CPU/RAM, database connections and egress are monitored.
- Load tests cover feed, search, upload, playback and comments.
- Rollback and incident procedures are documented.
