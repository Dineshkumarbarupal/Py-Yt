from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.models import Comment, User, Video
from db.session import get_db
from py.dependencies import get_current_user

router = APIRouter(prefix="/comments")

class CommentCreate(BaseModel):
    video_id: str
    body: str = Field(min_length=1, max_length=5000)
    parent_comment_id: str | None = None

@router.get("/video/{video_id}")
def list_comments(video_id: str, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video or video.status != "published" or video.visibility != "public":
        raise HTTPException(status_code=404, detail="Video not found.")
    rows = db.scalars(select(Comment).where(Comment.video_id == video_id, Comment.status == "visible").order_by(Comment.created_at.desc()).limit(100)).all()
    return {"items": [{"id": c.id, "user_id": c.user_id, "body": c.body, "parent_comment_id": c.parent_comment_id, "created_at": c.created_at} for c in rows]}

@router.post("", status_code=201)
def create_comment(payload: CommentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    video = db.get(Video, payload.video_id)
    if not video or video.status != "published" or video.visibility != "public":
        raise HTTPException(status_code=404, detail="Video not found.")
    if payload.parent_comment_id:
        parent = db.get(Comment, payload.parent_comment_id)
        if not parent or parent.video_id != video.id:
            raise HTTPException(status_code=404, detail="Parent comment not found.")
    comment = Comment(user_id=user.id, video_id=video.id, body=payload.body.strip(), parent_comment_id=payload.parent_comment_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {"id": comment.id, "body": comment.body, "created_at": comment.created_at}
