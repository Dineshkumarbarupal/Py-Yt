from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from db.models import Video, VideoReaction, WatchHistory, User
from db.session import get_db
from core.dependencies import get_current_user

router = APIRouter(prefix="/engagement")

class ReactionInput(BaseModel):
    reaction: str = Field(pattern="^(like|dislike)$")

class WatchProgressInput(BaseModel):
    progress_seconds: int = Field(ge=0, le=86400)

@router.put("/videos/{video_id}/reaction")
def set_reaction(video_id: str, payload: ReactionInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    video = db.get(Video, video_id)
    if not video or video.status != "published" or video.visibility != "public":
        raise HTTPException(status_code=404, detail="Video not found.")
    row = db.scalar(select(VideoReaction).where(VideoReaction.user_id == user.id, VideoReaction.video_id == video_id))
    if row:
        row.reaction = payload.reaction
    else:
        db.add(VideoReaction(user_id=user.id, video_id=video_id, reaction=payload.reaction))
    db.commit()
    return {"video_id": video_id, "reaction": payload.reaction}

@router.delete("/videos/{video_id}/reaction", status_code=204)
def remove_reaction(video_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(VideoReaction).where(VideoReaction.user_id == user.id, VideoReaction.video_id == video_id))
    if row:
        db.delete(row)
        db.commit()
    return None

@router.post("/videos/{video_id}/history")
def save_watch_progress(video_id: str, payload: WatchProgressInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    video = db.get(Video, video_id)
    if not video or video.status != "published" or video.visibility != "public":
        raise HTTPException(status_code=404, detail="Video not found.")
    row = db.scalar(select(WatchHistory).where(WatchHistory.user_id == user.id, WatchHistory.video_id == video_id))
    if row:
        row.progress_seconds = payload.progress_seconds
        row.last_watched_at = datetime.utcnow()
    else:
        db.add(WatchHistory(user_id=user.id, video_id=video_id, progress_seconds=payload.progress_seconds))
    db.commit()
    return {"status": "saved"}

@router.get("/history")
def watch_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(WatchHistory, Video).join(Video, WatchHistory.video_id == Video.id)
        .where(WatchHistory.user_id == user.id)
        .order_by(desc(WatchHistory.last_watched_at)).limit(100)
    ).all()
    return {"items": [{"video_id": video.id, "title": video.title, "progress_seconds": item.progress_seconds, "last_watched_at": item.last_watched_at} for item, video in rows]}
