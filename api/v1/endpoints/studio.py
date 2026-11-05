from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session
from db.models import Comment, Subscription, User, Video
from db.session import get_db
from core.dependencies import get_current_user
from services.creator import get_owned_channel

router = APIRouter(prefix="/studio")

@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    channel = get_owned_channel(db, user)
    published_count = db.scalar(
        select(func.count(Video.id)).where(Video.channel_id == channel.id, Video.status == "published")
    ) or 0
    draft_count = db.scalar(
        select(func.count(Video.id)).where(Video.channel_id == channel.id, Video.status.in_(["draft", "ready", "uploading"]))
    ) or 0
    total_views = db.scalar(
        select(func.coalesce(func.sum(Video.view_count), 0)).where(Video.channel_id == channel.id)
    ) or 0
    subscriber_count = db.scalar(
        select(func.count(Subscription.id)).where(Subscription.channel_id == channel.id)
    ) or 0
    comment_count = db.scalar(
        select(func.count(Comment.id))
        .join(Video, Comment.video_id == Video.id)
        .where(Video.channel_id == channel.id, Comment.status == "visible")
    ) or 0
    return {
        "channel": {"id": channel.id, "handle": channel.handle, "name": channel.name},
        "published_videos": published_count,
        "drafts_and_processing": draft_count,
        "total_views": total_views,
        "subscribers": subscriber_count,
        "visible_comments": comment_count,
    }

@router.get("/videos")
def creator_videos(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=200),
    status_filter: str | None = Query(default=None, alias="status", pattern="^(draft|uploading|ready|published|failed|deleted|removed)$"),
    visibility: str | None = Query(default=None, pattern="^(public|unlisted|private)$"),
    video_format: str | None = Query(default=None, pattern="^(standard|short)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    channel = get_owned_channel(db, user)
    conditions = [Video.channel_id == channel.id]
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        conditions.append(or_(Video.title.ilike(pattern), Video.description.ilike(pattern)))
    if status_filter:
        conditions.append(Video.status == status_filter)
    else:
        conditions.append(Video.status != "deleted")
    if visibility:
        conditions.append(Video.visibility == visibility)
    if video_format:
        conditions.append(Video.video_format == video_format)

    total_count = db.scalar(
        select(func.count(Video.id)).where(*conditions)
    ) or 0
    videos = db.scalars(
        select(Video)
        .where(*conditions)
        .order_by(desc(Video.created_at), desc(Video.id))
        .offset(offset)
        .limit(limit)
    ).all()
    return {
        "items": [
            {
                "id": video.id,
                "title": video.title,
                "description": video.description,
                "category": video.category,
                "video_format": video.video_format,
                "visibility": video.visibility,
                "status": video.status,
                "view_count": video.view_count,
                "created_at": video.created_at,
                "published_at": video.published_at,
            }
            for video in videos
        ],
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "next_offset": offset + len(videos) if offset + len(videos) < total_count else None,
    }

@router.get("/analytics")
def creator_analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    channel = get_owned_channel(db, user)
    videos = db.execute(
        select(Video.id, Video.title, Video.view_count, Video.published_at)
        .where(Video.channel_id == channel.id, Video.status == "published")
        .order_by(desc(Video.view_count), desc(Video.published_at))
        .limit(10)
    ).all()
    return {
        "total_views": db.scalar(
            select(func.coalesce(func.sum(Video.view_count), 0)).where(Video.channel_id == channel.id)
        ) or 0,
        "published_videos": db.scalar(
            select(func.count(Video.id)).where(Video.channel_id == channel.id, Video.status == "published")
        ) or 0,
        "top_videos": [
            {"id": video_id, "title": title, "view_count": view_count, "published_at": published_at}
            for video_id, title, view_count, published_at in videos
        ],
        "note": "View counts are basic counters. Audience retention, unique viewers, traffic sources and revenue analytics are not implemented yet.",
    }

@router.get("/comments")
def creator_comments(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    channel = get_owned_channel(db, user)
    rows = db.execute(
        select(Comment, Video, User)
        .join(Video, Comment.video_id == Video.id)
        .join(User, Comment.user_id == User.id)
        .where(Video.channel_id == channel.id)
        .order_by(desc(Comment.created_at))
        .limit(limit)
    ).all()
    return {
        "items": [
            {
                "id": comment.id,
                "video_id": video.id,
                "video_title": video.title,
                "display_name": author.display_name,
                "body": comment.body,
                "status": comment.status,
                "created_at": comment.created_at,
            }
            for comment, video, author in rows
        ]
    }

class CommentModeration(BaseModel):
    status: str = Field(pattern="^(visible|hidden)$")

@router.patch("/comments/{comment_id}")
def moderate_comment(
    comment_id: str,
    payload: CommentModeration,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    channel = get_owned_channel(db, user)
    row = db.execute(
        select(Comment, Video)
        .join(Video, Comment.video_id == Video.id)
        .where(Comment.id == comment_id, Video.channel_id == channel.id)
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Comment not found.")
    comment, _video = row
    comment.status = payload.status
    db.commit()
    return {"id": comment.id, "status": comment.status}
