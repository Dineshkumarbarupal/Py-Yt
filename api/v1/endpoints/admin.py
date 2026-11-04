from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from db.models import Channel, Comment, ContentReport, User, Video
from db.session import get_db
from core.dependencies import get_current_user

router = APIRouter(prefix="/admin")

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return user

@router.get("/reports")
def list_reports(
    status: str = Query(default="open", pattern="^(open|reviewing|actioned|dismissed|all)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    statement = select(ContentReport, User).join(User, ContentReport.reporter_id == User.id)
    if status != "all":
        statement = statement.where(ContentReport.status == status)
    rows = db.execute(
        statement.order_by(desc(ContentReport.created_at)).offset(offset).limit(limit)
    ).all()
    items = []
    for report, reporter in rows:
        target_url = "/admin/moderation"
        if report.target_type == "video":
            target_url = f"/watch/{report.target_id}"
        elif report.target_type == "comment":
            comment = db.get(Comment, report.target_id)
            video = db.get(Video, comment.video_id) if comment else None
            if video:
                target_url = f"/watch/{video.id}#comment-{report.target_id}"
        items.append(
            {
                "id": report.id,
                "target_type": report.target_type,
                "target_id": report.target_id,
                "target_url": target_url,
                "reason": report.reason,
                "details": report.details,
                "status": report.status,
                "reporter": reporter.display_name,
                "created_at": report.created_at,
                "resolution_note": report.resolution_note,
            }
        )
    return {"items": items}

class ReportReview(BaseModel):
    status: str = Field(pattern="^(reviewing|actioned|dismissed)$")
    resolution_note: str = Field(default="", max_length=500)

@router.patch("/reports/{report_id}")
def review_report(
    report_id: str,
    payload: ReportReview,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    report = db.get(ContentReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    if payload.status == "actioned":
        if report.target_type == "video":
            video = db.get(Video, report.target_id)
            if video and video.status == "published":
                video.status = "removed"
                video.visibility = "private"
        elif report.target_type == "comment":
            comment = db.get(Comment, report.target_id)
            if comment:
                comment.status = "hidden"

    report.status = payload.status
    report.reviewer_id = admin.id
    report.resolution_note = payload.resolution_note.strip()
    report.reviewed_at = datetime.utcnow()
    db.commit()
    return {"id": report.id, "status": report.status, "reviewed_at": report.reviewed_at}
