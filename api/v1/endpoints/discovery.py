from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.session import get_db
from services.catalog import public_feed, search_public_videos

router = APIRouter()

@router.get("/feed")
def feed(
    category: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=24, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return {
        "items": public_feed(db, category=category, limit=limit),
        "feed_type": "latest_public",
        "category": category or "All",
    }

@router.get("/search")
def search_videos(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=24, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None, max_length=40),
    db: Session = Depends(get_db),
):
    return {
        "query": q,
        "items": search_public_videos(
            db,
            query=q,
            category=category,
            limit=limit,
            offset=offset,
        ),
        "limit": limit,
        "offset": offset,
        "category": category or "All",
    }
