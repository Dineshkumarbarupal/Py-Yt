from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import desc, func, select, update
from sqlalchemy.orm import Session
from db.models import Channel, Notification, User
from db.session import get_db
from core.dependencies import get_current_user

router = APIRouter(prefix="/notifications")

@router.get("")
def list_notifications(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    statement = select(Notification).where(Notification.recipient_id == user.id)
    if unread_only:
        statement = statement.where(Notification.is_read.is_(False))
    rows = db.scalars(
        statement.order_by(desc(Notification.created_at), desc(Notification.id)).offset(offset).limit(limit)
    ).all()
    unread_count = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.recipient_id == user.id,
            Notification.is_read.is_(False),
        )
    ) or 0
    channel_ids = [item.entity_id for item in rows if item.entity_type == "channel" and item.entity_id]
    handles = {}
    if channel_ids:
        channels = db.scalars(select(Channel).where(Channel.id.in_(channel_ids))).all()
        handles = {channel.id: channel.handle for channel in channels}
    return {
        "items": [
            {
                "id": item.id,
                "type": item.notification_type,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "message": item.message,
                "is_read": item.is_read,
                "created_at": item.created_at,
                "url": (
                    f"/watch/{item.entity_id}" if item.entity_type == "video" and item.entity_id
                    else f"/@{handles[item.entity_id]}" if item.entity_type == "channel" and item.entity_id in handles
                    else "/notifications"
                ),
            }
            for item in rows
        ],
        "unread_count": unread_count,
        "limit": limit,
        "offset": offset,
    }

@router.post("/read-all", status_code=204)
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(
        update(Notification)
        .where(Notification.recipient_id == user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return Response(status_code=204)

@router.post("/{notification_id}/read", status_code=204)
def mark_read(
    notification_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_id == user.id,
        )
    )
    if not item:
        raise HTTPException(status_code=404, detail="Notification not found.")
    if not item.is_read:
        item.is_read = True
        db.commit()
    return Response(status_code=204)
