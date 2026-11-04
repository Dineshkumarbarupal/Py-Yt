from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.models import Channel, User

def get_owned_channel(db: Session, user: User) -> Channel:
    channel = db.scalar(select(Channel).where(Channel.owner_id == user.id))
    if not channel:
        raise HTTPException(status_code=404, detail="Creator channel not found.")
    return channel
