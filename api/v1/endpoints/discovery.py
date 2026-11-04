from fastapi import APIRouter, Query
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session
from fastapi import Depends
from db.models import Channel, Video
from db.session import get_db

router = APIRouter()

def _items(rows):
    return [{
        "id": video.id,
        "title": video.title,
        "category": video.category,
        "thumbnail_url": video.thumbnail_url,
        "duration_seconds": video.duration_seconds,
        "view_count": video.view_count,
        "channel_name": channel.name,
        "channel_handle": channel.handle,
        "published_at": video.published_at,
    } for video, channel in rows]

@router.get("/feed")
def feed(category: str | None = Query(default=None, max_length=40), limit: int = Query(default=24, ge=1, le=50), db: Session = Depends(get_db)):
    statement = select(Video, Channel)
        .join(Channel, Video.channel_id == Channel.id)
        .where(Video.status == "published", Video.visibility == "public")
        .order_by(desc(Video.published_at), desc(Video.created_at))
    if category and category != "All":
        statement = statement.where(Video.category == category)
    rows = db.execute(statement.order_by(desc(Video.published_at), desc(Video.created_at)).limit(limit)).all()
    return {"items": _items(rows), "feed_type": "latest_public", "category": category or "All"}

@router.get("/search")
def search_videos(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=24, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None, max_length=40),
    db: Session = Depends(get_db),
):
    pattern = f"%{q.strip()}%"
    statement = select(Video, Channel)
        .join(Channel, Video.channel_id == Channel.id)
        .where(
            Video.status == "published",
            Video.visibility == "public",
            or_(Video.title.ilike(pattern), Video.description.ilike(pattern), Channel.name.ilike(pattern)),
        )
        .order_by(desc(Video.published_at), desc(Video.created_at))
    if category and category != "All":
        statement = statement.where(Video.category == category)
    rows = db.execute(statement.order_by(desc(Video.published_at), desc(Video.created_at)).offset(offset).limit(limit)).all()
    return {"query": q, "items": _items(rows), "limit": limit, "offset": offset, "category": category or "All"}
