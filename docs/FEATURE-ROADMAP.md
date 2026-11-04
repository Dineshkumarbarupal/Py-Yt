# Py-Yt Product Feature Inventory

Py-Yt is an independent video platform inspired by YouTube's product categories. It does not reproduce YouTube's proprietary backend, private algorithms, licensed catalog or all region-specific features.

**Status key:** Implemented in code = source files and routes exist; verification pending = not yet demonstrated by successful complete CI/runtime verification; Planned = not implemented.

## Viewer experience
| Feature | Current status |
|---|---|
| Home feed, responsive navigation and category chips | Implemented in code |
| Category-filtered feed and local catalog search | Implemented in code |
| Watch page and signed playback URL | Implemented in code; object storage configuration required |
| Registration, login, logout and current account | Implemented in code |
| Public creator channel page | Implemented in code |
| Subscribe/unsubscribe and subscriptions list page | Implemented in code |
| Playlists: create, list, view and add videos | Implemented in code |
| Comments and threaded reply storage | Basic create/list API and comment UI |
| Like/dislike reactions | API implemented |
| Watch history and progress | API and personal history page implemented |
| Watch Later and Liked videos library | API and personal library page implemented |
| Playback speed, quality selector, chapters, captions UI, mini-player, theater mode, keyboard shortcuts, picture-in-picture | Planned |
| Sharing, reporting, user blocking and privacy controls | Planned |
| Personalized recommendations and “not interested” controls | Planned |

## Shorts and live
| Feature | Current status |
|---|---|
| Vertical short-video feed and upload presets | Planned |
| Shorts-specific duration/format constraints | Planned |
| Live stream scheduling and stream keys | Planned |
| Live ingest, transcoding, low-latency playback and real-time chat | Planned |
| Live chat moderation, clips and stream analytics | Planned |

## Creator Studio
| Feature | Current status |
|---|---|
| Creator Studio dashboard, content, analytics, comments and upload pages | Implemented in code |
| Direct-to-object-storage upload using presigned PUT | Implemented in code; bucket setup and E2E test pending |
| Upload metadata verification and publish lifecycle | Implemented in code; security checks still need expansion |
| Video title/category/visibility editing and owner-only deletion | Basic API and Studio UI implemented |
| Custom thumbnails, scheduled publishing, captions, chapters, end screens/cards | Planned |
| Basic creator analytics: total view counters and top videos | Implemented in code |
| Advanced retention, traffic sources and audience analytics | Planned |
| Creator hide/restore comment controls | Basic API and UI implemented |
| Advanced comment filters, automated moderation queue and pinned comments | Planned |
| A/B thumbnail/title experiments | Planned |
| Copyright/rights workflow | Planned; legal and technical review required |
| Community posts, memberships, merch, tips and ad revenue | Planned; payment, tax, eligibility and policy integrations required |

## Platform administration and safety
- Admin RBAC and staff roles: planned.
- User/content reports and moderation queue: planned.
- Audit logs, appeals, abuse detection, anti-spam and rate limiting: planned.
- Account recovery, email verification, MFA/passkeys and OAuth sign-in: planned.
- Age-appropriate/supervised experiences, localization and accessibility audits: planned.

## Advanced discovery and AI
- Custom feeds and explainable ranking controls: planned.
- AI-assisted discovery, creator ideation, captions/dubbing or editing: planned, consent-based and provider-policy compliant.
- Recommendations must be evaluated for safety, relevance, creator fairness and user controls.

## Four development phases
1. **Phase 1 — Foundation/MVP:** identity, channels, catalog, feed/search, upload/playback, playlists, subscriptions and basic engagement; MySQL/Alembic, tests, Docker and deployment.
2. **Phase 2 — Advanced:** Redis, background workers, FFmpeg transcoding, resumable multipart uploads, CDN, live MVP, analytics, notifications, moderation workers and load tests.
3. **Phase 3 — Enterprise:** justified service extraction, multi-tenant/organization tools where useful, HA database/replicas, advanced RBAC, observability, DR and governance.
4. **Phase 4 — Global:** multi-region media delivery/ingest, global routing, event-driven pipelines, regional data controls and tested DR.

Capacity targets require explicit concurrency/RPS definitions, workload modelling and repeatable load tests. No capacity is certified by this roadmap.
