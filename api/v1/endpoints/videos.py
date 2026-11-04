from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session
from db.models import Channel, Subscription, Video, User
from services.notifications import notify
from db.session import get_db
from core.dependencies import get_current_user, get_optional_user
from core.media_storage import MediaStorageNotConfigured, create_playback_url, delete_object
from botocore.exceptions import BotoCoreError, ClientError

router = APIRouter(prefix="/videos")

class VideoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    category: str = Field(default="General", pattern="^(General|Music|Gaming|Technology|Learning|Live|Comedy|Sports|News|Entertainment)$")
    video_format: str = Field(default="standard", pattern="^(standard|short)$")
    source_url: HttpUrl | None = None
    thumbnail_url: HttpUrl | None = None

class VideoPublish(BaseModel):
    visibility: str = Field(default="public", pattern="^(public|unlisted|private)$")

class VideoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    category: str | None = Field(default=None, pattern="^(General|Music|Gaming|Technology|Learning|Live|Comedy|Sports|News|Entertainment)$")
    video_format: str | None = Field(default=None, pattern="^(standard|short)$")
    visibility: str | None = Field(default=None, pattern="^(public|unlisted|private)$")

def _public_query():
    return select(Video, Channel, User).join(Channel, Video.channel_id == Channel.id).join(User, Channel.owner_id == User.id).where(
        Video.status == "published", Video.visibility == "public"
    )

@router.get("")
def list_videos(
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=24, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    statement = _public_query()
    if q:
        pattern = f"%{q.strip()}%"
        statement = statement.where(or_(Video.title.ilike(pattern), Video.description.ilike(pattern), Channel.name.ilike(pattern)))
    rows = db.execute(statement.order_by(desc(Video.published_at), desc(Video.created_at)).offset(offset).limit(limit)).all()
    return {"items": [
        {"id": v.id, "title": v.title, "description": v.description, "category": v.category, "thumbnail_url": v.thumbnail_url,
         "duration_seconds": v.duration_seconds, "video_format": v.video_format, "view_count": v.view_count, "channel_id": c.id,
         "channel_name": c.name, "channel_handle": c.handle, "published_at": v.published_at}
        for v, c, _owner in rows
    ], "limit": limit, "offset": offset}

@router.get("/mine")
def my_videos(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    channel = db.scalar(select(Channel).where(Channel.owner_id == user.id))
    if not channel:
        return {"items": []}
    rows = db.scalars(select(Video).where(Video.channel_id == channel.id).order_by(desc(Video.created_at))).all()
    return {"items": rows}

@router.post("", status_code=201)
def create_video(payload: VideoCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    channel = db.scalar(select(Channel).where(Channel.owner_id == user.id))
    if not channel:
        raise HTTPException(status_code=404, detail="Create a channel before adding a video.")
    video = Video(
        channel_id=channel.id, title=payload.title.strip(), description=payload.description.strip(),
        source_url=str(payload.source_url) if payload.source_url else None,
        category=payload.category,
        video_format=payload.video_format,
        thumbnail_url=str(payload.thumbnail_url) if payload.thumbnail_url else None,
        status="draft", visibility="private",
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video

@router.get("/{video_id}")
def get_video(video_id: str, db: Session = Depends(get_db)):
    row = db.execute(select(Video, Channel).join(Channel, Video.channel_id == Channel.id).where(Video.id == video_id)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Video not found.")
    video, channel = row
    if video.visibility == "private" or video.status != "published":
        raise HTTPException(status_code=404, detail="Video not found.")
    return {"id": video.id, "title": video.title, "description": video.description,
            "source_url": video.source_url, "thumbnail_url": video.thumbnail_url,
            "duration_seconds": video.duration_seconds, "video_format": video.video_format, "view_count": video.view_count,
            "channel": {"id": channel.id, "name": channel.name, "handle": channel.handle}}

@router.patch("/{video_id}")
def update_video(video_id: str, payload: VideoUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    video = db.get(Video, video_id)
    channel = db.scalar(select(Channel).where(Channel.owner_id == user.id))
    if not video or not channel or video.channel_id != channel.id:
        raise HTTPException(status_code=404, detail="Video not found.")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(video, key, value)
    db.commit()
    db.refresh(video)
    return video

@router.delete("/{video_id}", status_code=204)
def delete_video(
    video_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    video = db.get(Video, video_id)
    channel = db.scalar(select(Channel).where(Channel.owner_id == user.id))
    if not video or not channel or video.channel_id != channel.id:
        raise HTTPException(status_code=404, detail="Video not found.")
    if video.status == "deleted":
        return Response(status_code=204)
    if video.storage_key:
        try:
            delete_object(video.storage_key)
        except MediaStorageNotConfigured as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        except (BotoCoreError, ClientError):
            raise HTTPException(status_code=502, detail="The media object could not be deleted. The video remains unchanged.")
    video.status = "deleted"
    video.visibility = "private"
    db.commit()
    return Response(status_code=204)

@router.post("/{video_id}/publish")
def publish_video(video_id: str, payload: VideoPublish, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    video = db.get(Video, video_id)
    channel = db.scalar(select(Channel).where(Channel.owner_id == user.id))
    if not video or not channel or video.channel_id != channel.id:
        raise HTTPException(status_code=404, detail="Video not found.")
    if not video.storage_key or video.status != "ready":
        raise HTTPException(status_code=409, detail="A completed and verified media upload is required before publishing.")
    video.status = "published"
    video.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
    video.visibility = payload.visibility
    if video.visibility == "public":
        subscriber_ids = db.scalars(
            select(Subscription.subscriber_id).where(Subscription.channel_id == channel.id)
        ).all()
        for recipient_id in subscriber_ids:
            notify(
                db,
                recipient_id=recipient_id,
                actor_id=user.id,
                notification_type="new_video",
                entity_type="video",
                entity_id=video.id,
                message=f"{channel.name} published a new video: {video.title}",
            )
    db.commit()
    return {"id": video.id, "status": video.status, "visibility": video.visibility}

@router.get("/{video_id}/playback")
def get_playback(
    video_id: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    video = db.get(Video, video_id)
    if not video or video.status not in {"ready", "published"}:
        raise HTTPException(status_code=404, detail="Video is not ready for playback.")
    channel = db.get(Channel, video.channel_id)
    is_owner = bool(user and channel and channel.owner_id == user.id)
    if video.status != "published" and not is_owner:
        raise HTTPException(status_code=404, detail="Video not found.")
    if video.visibility == "private" and not is_owner:
        raise HTTPException(status_code=404, detail="Video not found.")
    if not video.storage_key:
        raise HTTPException(status_code=409, detail="This video has no verified media object.")
    try:
        url = create_playback_url(video.storage_key, expires_in=600)
    except MediaStorageNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (BotoCoreError, ClientError):
        raise HTTPException(status_code=502, detail="Could not create a playback URL.")
    return {"video_id": video.id, "playback_url": url, "expires_in": 600, "mime_type": video.mime_type}

@router.post("/{video_id}/view")
def record_view(video_id: str, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video or video.status != "published" or video.visibility != "public":
        raise HTTPException(status_code=404, detail="Video not found.")
    video.view_count += 1
    db.commit()
    return {"view_count": video.view_count}
