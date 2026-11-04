from fastapi import APIRouter
from api.v1.endpoints import health, discovery

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
