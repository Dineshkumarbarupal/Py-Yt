from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from db.models import User, Video, VideoReaction, WatchHistory, WatchLater, Channel
from db.session import get_db
from core.dependencies import get_current_user

router = APIRouter(prefix="/library")

def _video_item(video: Video, channel: Channel) -> dict:
    return {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "thumbnail_url": video.thumbnail_url,
        "category": video.category,
        "view_count": video.view_count,
        "channel_name": channel.name,
        "channel_handle": channel.handle,
        "published_at": video.published_at,
    }

@router.get("/watch-later")
def list_watch_later(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(WatchLater, Video, Channel)
        .join(Video, WatchLater.video_id == Video.id)
        .join(Channel, Video.channel_id == Channel.id)
        .where(WatchLater.user_id == user.id, Video.status == "published", Video.visibility == "public")
        .order_by(desc(WatchLater.created_at))
        .limit(200)
    ).all()
    return {"items": [_video_item(video, channel) for _saved, video, channel in rows]}

@router.post("/watch-later/{video_id}", status_code=201)
def add_watch_later(video_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    video = db.get(Video, video_id)
    if not video or video.status != "published" or video.visibility != "public":
        raise HTTPException(status_code=404, detail="Video not found.")
    existing = db.scalar(
        select(WatchLater).where(WatchLater.user_id == user.id, WatchLater.video_id == video.id)
    )
    if existing:
        return {"status": "already_saved"}
    db.add(WatchLater(user_id=user.id, video_id=video.id))
    db.commit()
    return {"status": "saved"}

@router.delete("/watch-later/{video_id}", status_code=204)
def remove_watch_later(video_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    saved = db.scalar(
        select(WatchLater).where(WatchLater.user_id == user.id, WatchLater.video_id == video_id)
    )
    if saved:
        db.delete(saved)
        db.commit()
    return None

@router.get("/liked")
def list_liked_videos(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(VideoReaction, Video, Channel)
        .join(Video, VideoReaction.video_id == Video.id)
        .join(Channel, Video.channel_id == Channel.id)
        .where(
            VideoReaction.user_id == user.id,
            VideoReaction.reaction == "like",
            Video.status == "published",
            Video.visibility == "public",
        )
        .order_by(desc(VideoReaction.created_at))
        .limit(200)
    ).all()
    return {"items": [_video_item(video, channel) for _reaction, video, channel in rows]}

@router.get("/history")
def list_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(WatchHistory, Video, Channel)
        .join(Video, WatchHistory.video_id == Video.id)
        .join(Channel, Video.channel_id == Channel.id)
        .where(WatchHistory.user_id == user.id)
        .order_by(desc(WatchHistory.last_watched_at))
        .limit(200)
    ).all()
    return {
        "items": [
            {
                **_video_item(video, channel),
                "progress_seconds": history.progress_seconds,
                "last_watched_at": history.last_watched_at,
            }
            for history, video, channel in rows
        ]
    }
