# Security Notes

## Implemented foundations
- Argon2 password hashing.
- Signed expiring JWT in an HttpOnly cookie.
- SameSite cookie policy and production secure-cookie setting.
- Double-submit CSRF cookie/header check for unsafe methods when a session cookie is present.
- Pydantic request validation and SQLAlchemy parameterized operations.
- Server-generated video object keys.
- Presigned PUT URLs for supported video MIME types.
- Upload completion checks storage ContentLength and ContentType; mismatched uploaded objects are rejected and deletion is attempted.
- Private video playback requires channel-owner identity and returns an expiring signed URL.
- Basic response security headers.

## Required before production launch
- Generate a unique high-entropy SECRET_KEY and rotate it through secret management.
- Require HTTPS and set SESSION_COOKIE_SECURE=true.
- Review CSRF behavior behind the production proxy and test same-origin and cross-origin requests.
- Restrict CORS to known frontend origins; do not use wildcard origins with credentials.
- Configure a scoped object-storage key, bucket CORS, encryption and lifecycle.
- Add per-user/IP rate limits for login, comments, subscriptions, upload presign and view endpoints.
- Add email verification, password reset and MFA/passkeys before public launch.
- Add ownership and role checks to every new API.
- Add upload signature validation, malware/content scanning and media transcoding before public publication.
- Add request IDs, audit logs, alerting and secret redaction.
- Test SQL backups, object-store backups/versioning, restoration and key rotation.
- Add content reporting, moderation, copyright and privacy/legal workflows.

## Media safety
The presign API validates the declared file size against the configured maximum, then verifies the uploaded object's actual ContentLength and ContentType. With presigned PUT, a malicious client may still attempt a larger transfer before completion rejects it; production must add upload-rate limits, abuse controls and storage-cost monitoring. Browser MIME headers are not proof of file contents. Production must inspect file signatures and scan/transcode uploaded files in a worker before allowing public playback.

## Trust boundaries
Treat titles, descriptions, comments, thumbnails, external URLs and provider metadata as untrusted. Escape them on output, restrict server-side outbound URL fetches and add SSRF controls to any future URL preview feature.
