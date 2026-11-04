from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from db.models import Channel, Subscription, User, Video
from services.notifications import notify
from db.session import get_db
from core.dependencies import get_current_user

router = APIRouter(prefix="/subscriptions")

@router.get("")
def list_subscriptions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(Subscription, Channel)
        .join(Channel, Subscription.channel_id == Channel.id)
        .where(Subscription.subscriber_id == user.id)
        .order_by(Subscription.created_at.desc())
    ).all()
    return {
        "items": [
            {"channel_id": channel.id, "handle": channel.handle, "name": channel.name, "subscribed_at": subscription.created_at}
            for subscription, channel in rows
        ]
    }

@router.get("/feed")
def subscription_feed(
    limit: int = Query(default=24, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.execute(
        select(Video, Channel)
        .join(Channel, Video.channel_id == Channel.id)
        .join(Subscription, Subscription.channel_id == Channel.id)
        .where(
            Subscription.subscriber_id == user.id,
            Video.status == "published",
            Video.visibility == "public",
        )
        .order_by(desc(Video.published_at), desc(Video.created_at))
        .offset(offset)
        .limit(limit)
    ).all()
    return {
        "items": [
            {
                "id": video.id,
                "title": video.title,
                "thumbnail_url": video.thumbnail_url,
                "category": video.category,
                "view_count": video.view_count,
                "channel_name": channel.name,
                "channel_handle": channel.handle,
                "published_at": video.published_at,
            }
            for video, channel in rows
        ],
        "limit": limit,
        "offset": offset,
    }

@router.post("/{channel_id}", status_code=201)
def subscribe(channel_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")
    if channel.owner_id == user.id:
        raise HTTPException(status_code=409, detail="You cannot subscribe to your own channel.")
    existing = db.scalar(
        select(Subscription).where(
            Subscription.subscriber_id == user.id,
            Subscription.channel_id == channel_id,
        )
    )
    if existing:
        return {"status": "already_subscribed"}
    db.add(Subscription(subscriber_id=user.id, channel_id=channel_id))
    notify(
        db,
        recipient_id=channel.owner_id,
        actor_id=user.id,
        notification_type="new_subscriber",
        entity_type="channel",
        entity_id=channel.id,
        message=f"{user.display_name} subscribed to your channel.",
    )
    db.commit()
    return {"status": "subscribed"}

@router.delete("/{channel_id}", status_code=204)
def unsubscribe(channel_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    subscription = db.scalar(
        select(Subscription).where(
            Subscription.subscriber_id == user.id,
            Subscription.channel_id == channel_id,
        )
    )
    if subscription:
        db.delete(subscription)
        db.commit()
    return None
