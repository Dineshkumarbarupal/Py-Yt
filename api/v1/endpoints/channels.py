from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.models import Channel, User
from db.session import get_db
from py.dependencies import get_current_user

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
    return {"id": channel.id, "handle": channel.handle, "name": channel.name, "description": channel.description}
