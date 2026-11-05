# Py-Yt Product Feature Inventory

Py-Yt is an independent video platform inspired by YouTube's product categories. It does not reproduce YouTube's proprietary backend, private algorithms, licensed catalog or all region-specific features.

**Status key:** Implemented in code = source files and routes exist; verification pending = not yet demonstrated by successful complete CI/runtime verification; Planned = not implemented.

## Viewer experience
| Feature | Current status |
|---|---|
| Home feed, responsive navigation and category chips | Implemented in code |
| Category-filtered feed, local catalog search and public autocomplete | Implemented in code |
| Watch page and signed playback URL | Implemented in code; object storage configuration required |
| Registration, login, logout, current account, profile editing and password change | Implemented in code |
| Public creator channel page | Implemented in code |
| Subscribe/unsubscribe, subscriptions list and latest-from-subscriptions feed | Implemented in code |
| Playlists: create, list, view, add/remove videos, reorder, edit and delete | Implemented in code |
| Comments and threaded reply storage | Basic create/list API and comment UI |
| Like/dislike reactions and live count/state display | API and watch UI implemented |
| Watch history and progress | API and personal history page implemented |
| Watch Later and Liked videos library | API/UI support removal and unlike actions |
| Watch history | API/UI support individual removal and clear-all actions |
| In-app notifications for new videos, subscribers, comments and replies | Implemented in code with unread/read controls |
| Playback speed, theater mode, keyboard shortcuts, picture-in-picture, in-page mini-player, share, like/dislike, autoplay, latest Up next list and session Watch Queue | Implemented in code |
| Adaptive quality selector, chapters, caption/subtitle tracks and mini-player | Planned |
| Video/comment reporting and admin moderation queue | Basic implementation in code |
| Sharing | Implemented in code |
| User blocking, advanced privacy controls and appeals | Planned |
| Personalized recommendations and “not interested” controls | Planned |

## Shorts and live
| Feature | Current status |
|---|---|
| Standard/Shorts format metadata, upload selector and vertical scroll-snap feed | Basic implementation in code |
| Server-side Shorts duration validation, FFmpeg portrait renditions and cover-frame extraction | Planned |
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
- Admin role check, admin-only moderation APIs and console bootstrap for existing users: basic implementation in code. Granular staff roles and permission matrix: planned.
- Viewer reporting for public videos and visible comments, admin-only moderation queue, dismiss/review/action controls: basic implementation in code.
- Appeals, reviewer audit trail, automated abuse detection, copyright/takedown workflow and policy automation: planned.
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
