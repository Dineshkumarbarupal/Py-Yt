# Deployment Guide

## Recommended architecture and cost notes (checked 4 Nov 2026)

- **Application + MySQL:** Railway is the recommended first host for this FastAPI/MySQL MVP. Railway's published Hobby plan has a $5/month minimum usage commitment and Pro has a $20/month minimum; actual resource use and outbound traffic are billed separately. Start with Hobby for a private beta, then review usage before inviting a larger audience. Source: https://railway.com/pricing
- **Video object storage:** Use Cloudflare R2 Standard for original video objects and signed playback. Published Standard storage is $0.015 per GB-month, standard egress is free, and the listed monthly free allowance includes 10 GB-month storage plus Class A/B operation allowances. Request charges still apply beyond the free tier. Source: https://developers.cloudflare.com/r2/pricing/
- **Why separate storage:** Video delivery can generate much more traffic than API calls. Keep file bytes on R2 and use signed URLs; do not proxy playback through FastAPI/Railway. This avoids using app-server egress for every watch.
- **Alternative:** DigitalOcean App Platform plus Managed MySQL if you prefer a more traditional managed cloud setup. App Platform's small shared services start at $5/month, but production database charges, media storage and transfer are additional. Source: https://docs.digitalocean.com/products/app-platform/details/pricing/

These are published list prices checked on the date above, not a guaranteed monthly bill. Estimate using expected stored GB, upload operations, playback GB/month, concurrent streams, API CPU/RAM and database size. For a video platform, bandwidth/CDN and transcoding become material cost drivers.

## Recommended first host: Railway

For the current Phase 1 scope, Railway is the easiest initial target: it supports GitHub/Docker deployments and a MySQL service. The media bucket must be external object storage; do not use ephemeral app-disk storage for videos.

### Railway setup
1. Create a Railway project and connect your GitHub account.
2. Add a MySQL service.
3. Add a service from GitHub and select Dineshkumarbarupal/Py-Yt on branch main. Build using the root Dockerfile.
4. Set environment variables: APP_ENV=production, DEBUG=false, a unique random SECRET_KEY of at least 32 characters, CORS_ORIGINS set to your exact production origin (no wildcard), SESSION_COOKIE_SECURE=true and SESSION_COOKIE_SAMESITE=lax, DATABASE_URL using MySQL PyMySQL, MEDIA_BUCKET set to a private originals bucket, MEDIA_THUMBNAIL_BUCKET set to a separate public thumbnails bucket, MEDIA_ACCESS_KEY_ID/MEDIA_SECRET_ACCESS_KEY with access to both buckets, and MEDIA_PUBLIC_BASE_URL set to the HTTPS custom domain attached only to the public thumbnails bucket. The app now refuses to boot with unsafe production settings. Set DATABASE_URL using the private MySQL service variables, for example: mysql+pymysql://${{MySQL.MYSQLUSER}}:${{MySQL.MYSQLPASSWORD}}@${{MySQL.MYSQLHOST}}:${{MySQL.MYSQLPORT}}/${{MySQL.MYSQLDATABASE}}. URL-encode special characters in the database password before assembling the URL.
5. Set the pre-deploy command to: alembic upgrade head.
6. Set the healthcheck path to /api/v1/ready (checks database connectivity), generate a domain, then attach your custom domain and HTTPS.
7. Configure MySQL backups/point-in-time recovery where available and test restoring a backup.
8. Configure object-storage CORS to allow PUT from your production origin and the Content-Type request header. Attach the R2 custom domain to the separate thumbnails bucket only and set MEDIA_PUBLIC_BASE_URL to that HTTPS origin. Never attach a public domain to MEDIA_BUCKET: keep original video objects private and serve them only with signed playback URLs. The app rejects identical MEDIA_BUCKET and MEDIA_THUMBNAIL_BUCKET values. Do not store video bytes in the app container.
9. Verify health and database readiness, login, upload, completion, publish, signed playback and database restore before public launch.

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

## Local test deployment

On your Windows development machine, install Docker Desktop and enable WSL 2 integration. Copy `.env.example` to `.env`, set non-default secrets and MySQL passwords, configure R2/S3 for uploads, then run `docker compose up --build`. The Compose `migrate` one-shot service applies Alembic migrations before the app is considered healthy; Nginx is exposed at `http://localhost`.

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
