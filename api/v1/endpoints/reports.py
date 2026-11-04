from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from db.models import Channel, Comment, ContentReport, User, Video
from db.session import get_db
from core.dependencies import get_current_user

router = APIRouter(prefix="/reports")

class ReportCreate(BaseModel):
    target_type: str = Field(pattern="^(video|comment)$")
    target_id: str = Field(min_length=1, max_length=36)
    reason: str = Field(pattern="^(spam|harassment|hate|violence|sexual_content|misinformation|copyright|privacy|other)$")
    details: str = Field(default="", max_length=2000)

@router.post("", status_code=201)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.target_type == "video":
        target = db.get(Video, payload.target_id)
        if not target or target.status != "published" or target.visibility != "public":
            raise HTTPException(status_code=404, detail="Video not found.")
    else:
        target = db.get(Comment, payload.target_id)
        if not target or target.status != "visible":
            raise HTTPException(status_code=404, detail="Comment not found.")
        video = db.get(Video, target.video_id)
        if not video or video.status != "published" or video.visibility != "public":
            raise HTTPException(status_code=404, detail="Comment not found.")

    existing = db.scalar(
        select(ContentReport).where(
            ContentReport.reporter_id == user.id,
            ContentReport.target_type == payload.target_type,
            ContentReport.target_id == payload.target_id,
        )
    )
    if existing:
        return {"id": existing.id, "status": "already_reported"}

    report = ContentReport(
        reporter_id=user.id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        reason=payload.reason,
        details=payload.details.strip(),
        status="open",
    )
    db.add(report)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"status": "already_reported"}
    db.refresh(report)
    return {"id": report.id, "status": report.status}
