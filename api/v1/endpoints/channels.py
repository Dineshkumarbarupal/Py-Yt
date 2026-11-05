from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from db.models import Channel, Subscription, User, Video
from db.session import get_db
from core.dependencies import get_current_user

router = APIRouter(prefix="/channels")

class ChannelUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=5000)

@router.get("/me")
def my_channel(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    channel = db.scalar(select(Channel).where(Channel.owner_id == user.id))
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")
    return channel

@router.patch("/me")
def update_my_channel(payload: ChannelUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    channel = db.scalar(select(Channel).where(Channel.owner_id == user.id))
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")
    channel.name = payload.name.strip()
    channel.description = payload.description.strip()
    db.commit()
    db.refresh(channel)
    return channel

@router.get("/{handle}")
def public_channel(handle: str, db: Session = Depends(get_db)):
    channel = db.scalar(select(Channel).where(Channel.handle == handle))
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")
    subscriber_count = db.scalar(
        select(func.count(Subscription.id)).where(Subscription.channel_id == channel.id)
    ) or 0
    video_count = db.scalar(
        select(func.count(Video.id)).where(
            Video.channel_id == channel.id,
            Video.status == "published",
            Video.visibility == "public",
        )
    ) or 0
    return {
        "id": channel.id,
        "handle": channel.handle,
        "name": channel.name,
        "description": channel.description,
        "subscriber_count": subscriber_count,
        "video_count": video_count,
    }
