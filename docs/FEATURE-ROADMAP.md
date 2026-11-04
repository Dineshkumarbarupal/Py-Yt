# Py-Yt Product Feature Inventory

Py-Yt is an independent video platform inspired by YouTube's product categories. It does not reproduce YouTube's proprietary backend, private algorithms, licensed catalog or every region-specific feature.

**Status key:** Implemented in repository = code exists; verification pending = no successful full test/deployment evidence yet; Planned = not implemented.

## Viewer experience
| Feature | Status |
|---|---|
| Home feed of public Py-Yt videos | Implemented; DB migration/test verification pending |
| Category chips and filtered feed | Implemented; test verification pending |
| Search across title, description and channel | Implemented; test verification pending |
| Watch page with signed media playback | Implemented; storage configuration required |
| Sign up, sign in, sign out and current user | Implemented; test verification pending |
| Channel page and profile editing | Basic API implemented; UI extension planned |
| Subscriptions | Basic list/subscribe/unsubscribe APIs implemented |
| Playlists | Create/list/get/add APIs implemented |
| Comments and replies | Basic create/list APIs implemented |
| Like/dislike reactions | Basic write/remove APIs implemented |
| Watch history and progress | Basic API implemented |
| Watch Later and Liked videos library UI | Planned |
| Playback speed, quality selector, chapters, captions UI, mini-player, theater mode, keyboard shortcuts, picture-in-picture | Planned |
| Share links, content reporting, user blocking and privacy controls | Planned |
| Personalized recommendations and “not interested” controls | Planned |

## Shorts and live
| Feature | Status |
|---|---|
| Vertical short-video feed and upload presets | Planned |
| Shorts-specific video duration/format constraints | Planned |
| Live stream scheduling and stream keys | Planned |
| Live ingest, transcoding, low-latency playback and real-time chat | Planned |
| Live chat moderation, clips and stream analytics | Planned |

## Creator Studio
| Feature | Status |
|---|---|
| Creator Studio landing page | Basic UI exists |
| Direct-to-object-storage upload | Implemented; storage configuration and end-to-end test pending |
| Upload size/MIME metadata verification | Implemented; provider test pending |
| Draft/ready/published lifecycle and visibility | Basic API implemented |
| Video metadata/category editing | Basic API implemented |
| Custom thumbnails, scheduled publishing, subtitles, chapters, end screens/cards | Planned |
| Creator analytics: views, watch time, retention, traffic sources and audience | Planned |
| Comment filters, moderation queue and pinned comments | Planned |
| A/B thumbnail/title experiments | Planned |
| Copyright/rights workflow | Planned; legal and technical review required |
| Community posts, memberships, merch, tipping and ad revenue | Planned; payment, tax, eligibility and policy integrations required |

## Platform administration and safety
- Admin RBAC and staff roles: planned.
- User/content reports and moderation queue: planned.
- Audit logs, appeals, abuse detection, anti-spam and rate limits: planned.
- Account recovery, email verification, MFA/passkeys and OAuth sign-in: planned.
- Age-appropriate/supervised experiences, localization and accessibility audits: planned.

## Advanced discovery and AI
- Custom feeds and explainable ranking controls: planned.
- AI-assisted discovery, creator ideation, captions/dubbing or editing: planned, consent-based and provider-policy compliant.
- Recommendation systems must be evaluated for safety, relevance, creator fairness and user controls.

## Four development phases
1. **Phase 1 — Foundation/MVP:** identity, channels, catalog, public feed/search, upload/playback, playlists, subscriptions and basic engagement; MySQL/Alembic; tests; Docker; deployment.
2. **Phase 2 — Advanced:** Redis, background workers, FFmpeg transcoding, resumable multipart uploads, CDN, live MVP, analytics, notification and moderation workers; load testing.
3. **Phase 3 — Enterprise:** service extraction when justified, multi-tenant/organization tools where useful, HA database/replicas, advanced RBAC, observability, disaster recovery and governance.
4. **Phase 4 — Global:** multi-region media delivery and ingest, global routing, event-driven pipelines, regional data controls and tested disaster recovery.

Capacity targets such as 10k/100k/1m/1b users per hour are planning goals only. They require explicit concurrency/RPS definitions, workload modelling and load tests. No capacity is certified by this roadmap.
