from fastapi import APIRouter
from api.v1.endpoints import auth, channels, comments, discovery, engagement, health, playlists, subscriptions, videos

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["authentication"])
api_router.include_router(channels.router, tags=["channels"])
api_router.include_router(videos.router, tags=["videos"])
api_router.include_router(playlists.router, tags=["playlists"])
api_router.include_router(subscriptions.router, tags=["subscriptions"])
api_router.include_router(comments.router, tags=["comments"])
api_router.include_router(engagement.router, tags=["engagement"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
