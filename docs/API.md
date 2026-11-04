# API Index (v1)

OpenAPI documentation is available at /docs in non-production environments.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /health | Process health |
| POST | /api/v1/auth/register | Register user and create initial channel |
| POST | /api/v1/auth/login | Sign in and set session cookies |
| POST | /api/v1/auth/logout | Clear session cookies |
| GET/PATCH | /api/v1/auth/me | Read/update current profile |
| POST | /api/v1/auth/change-password | Change password after current-password verification |
| GET/PATCH | /api/v1/channels/me | Read/update current channel |
| GET | /api/v1/channels/{handle} | Public channel profile |
| GET | /api/v1/videos | List public videos |
| GET | /api/v1/videos/mine | Current creator videos |
| POST | /api/v1/videos | Create private draft metadata |
| GET/PATCH | /api/v1/videos/{video_id} | Read/update video metadata |
| GET | /api/v1/videos/{video_id}/playback | Generate signed playback URL |
| POST | /api/v1/videos/{video_id}/publish | Publish verified upload |
| POST | /api/v1/videos/{video_id}/view | Increment public view counter |
| POST | /api/v1/uploads/presign | Create constrained direct-upload URL |
| POST | /api/v1/uploads/{video_id}/complete | Verify uploaded object |
| GET | /api/v1/discovery/feed | Latest public feed with category filter |
| GET | /api/v1/discovery/search | Search local catalog |
| GET | /api/v1/playlists/mine | Current user's playlists |
| POST | /api/v1/playlists | Create playlist |
| GET | /api/v1/playlists/{playlist_id} | Read accessible playlist |
| POST | /api/v1/playlists/{playlist_id}/items | Add video to playlist |
| GET | /api/v1/subscriptions | List subscriptions |
| POST/DELETE | /api/v1/subscriptions/{channel_id} | Subscribe/unsubscribe |
| GET | /api/v1/comments/video/{video_id} | List public video comments |
| POST | /api/v1/comments | Create comment/reply |
| PUT/DELETE | /api/v1/engagement/videos/{video_id}/reaction | Like/dislike or remove reaction |
| POST | /api/v1/engagement/videos/{video_id}/history | Save watch progress |
| GET | /api/v1/engagement/history | Current user's watch history |

Mutating authenticated requests require the CSRF header matching the pyyt_csrf cookie. API response fields may evolve until the Phase 1 contract is frozen.
