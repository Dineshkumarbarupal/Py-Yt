from sqlalchemy.orm import Session
from db.models import Notification

def notify(
    db: Session,
    *,
    recipient_id: str,
    actor_id: str | None,
    notification_type: str,
    entity_type: str,
    entity_id: str | None,
    message: str,
) -> None:
    if actor_id and actor_id == recipient_id:
        return
    db.add(
        Notification(
            recipient_id=recipient_id,
            actor_id=actor_id,
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message[:500],
        )
    )
