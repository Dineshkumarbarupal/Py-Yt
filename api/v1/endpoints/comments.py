from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.models import Channel, Comment, User, Video
from services.notifications import notify
from db.session import get_db
from core.dependencies import get_current_user

router = APIRouter(prefix="/comments")

class CommentCreate(BaseModel):
    video_id: str
    body: str = Field(min_length=1, max_length=5000)
    parent_comment_id: str | None = None

@router.get("/video/{video_id}")
def list_comments(video_id: str, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video or video.status != "published" or video.visibility == "private":
        raise HTTPException(status_code=404, detail="Video not found.")
    rows = db.execute(
        select(Comment, User)
        .join(User, Comment.user_id == User.id)
        .where(Comment.video_id == video_id, Comment.status == "visible")
        .order_by(Comment.created_at.desc())
        .limit(100)
    ).all()
    return {"items": [
        {
            "id": comment.id,
            "user_id": comment.user_id,
            "display_name": user.display_name,
            "body": comment.body,
            "parent_comment_id": comment.parent_comment_id,
            "created_at": comment.created_at,
        }
        for comment, user in rows
    ]}

@router.post("", status_code=201)
def create_comment(payload: CommentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    video = db.get(Video, payload.video_id)
    if not video or video.status != "published" or video.visibility == "private":
        raise HTTPException(status_code=404, detail="Video not found.")
    if payload.parent_comment_id:
        parent = db.get(Comment, payload.parent_comment_id)
        if not parent or parent.video_id != video.id:
            raise HTTPException(status_code=404, detail="Parent comment not found.")
    comment = Comment(
        user_id=user.id,
        video_id=video.id,
        body=payload.body.strip(),
        parent_comment_id=payload.parent_comment_id,
    )
    db.add(comment)
    channel = db.get(Channel, video.channel_id)
    recipient_ids = {channel.owner_id} if channel else set()
    parent = db.get(Comment, payload.parent_comment_id) if payload.parent_comment_id else None
    if parent:
        recipient_ids.add(parent.user_id)
    for recipient_id in recipient_ids:
        notify(
            db,
            recipient_id=recipient_id,
            actor_id=user.id,
            notification_type="new_comment" if not parent else "comment_reply",
            entity_type="video",
            entity_id=video.id,
            message=(
                f"{user.display_name} replied to your comment on {video.title}."
                if parent and recipient_id == parent.user_id
                else f"{user.display_name} commented on your video: {video.title}"
            ),
        )
    db.commit()
    db.refresh(comment)
    return {
        "id": comment.id,
        "body": comment.body,
        "display_name": user.display_name,
        "created_at": comment.created_at,
    }
