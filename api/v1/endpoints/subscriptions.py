from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.models import Channel, Subscription, User
from db.session import get_db
from py.dependencies import get_current_user

router = APIRouter(prefix="/subscriptions")

@router.get("")
def list_subscriptions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(select(Subscription, Channel).join(Channel, Subscription.channel_id == Channel.id).where(Subscription.subscriber_id == user.id).order_by(Subscription.created_at.desc())).all()
    return {"items": [{"channel_id": c.id, "handle": c.handle, "name": c.name, "subscribed_at": s.created_at} for s, c in rows]}

@router.post("/{channel_id}", status_code=201)
def subscribe(channel_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")
    if channel.owner_id == user.id:
        raise HTTPException(status_code=409, detail="You cannot subscribe to your own channel.")
    existing = db.scalar(select(Subscription).where(Subscription.subscriber_id == user.id, Subscription.channel_id == channel_id))
    if existing:
        return {"status": "already_subscribed"}
    db.add(Subscription(subscriber_id=user.id, channel_id=channel_id))
    db.commit()
    return {"status": "subscribed"}

@router.delete("/{channel_id}", status_code=204)
def unsubscribe(channel_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    subscription = db.scalar(select(Subscription).where(Subscription.subscriber_id == user.id, Subscription.channel_id == channel_id))
    if subscription:
        db.delete(subscription)
        db.commit()
    return None
