from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_optional_user
from db.models import Channel, User, Video, VideoChapter
from db.session import get_db

router = APIRouter(prefix="/videos")


class ChapterInput(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    start_seconds: int = Field(ge=0, le=86400)

    @model_validator(mode="after")
    def validate_title(self):
        if not self.title.strip():
            raise ValueError("Chapter title cannot be blank.")
        return self


class ChapterReplace(BaseModel):
    items: list[ChapterInput] = Field(max_length=100)


def _chapter_access(db: Session, video_id: str, user: User | None) -> tuple[Video, bool]:
    video = db.get(Video, video_id)
    if not video or video.status in {"deleted", "removed"}:
        raise HTTPException(status_code=404, detail="Video not found.")
    channel = db.get(Channel, video.channel_id)
    is_owner = bool(user and channel and channel.owner_id == user.id)
    if not is_owner and not (video.status == "published" and video.visibility in {"public", "unlisted"}):
        raise HTTPException(status_code=404, detail="Video not found.")
    return video, is_owner


def _serialize(chapter: VideoChapter) -> dict:
    return {
        "id": chapter.id,
        "title": chapter.title,
        "start_seconds": chapter.start_seconds,
    }


@router.get("/{video_id}/chapters")
def list_chapters(
    video_id: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    video, _is_owner = _chapter_access(db, video_id, user)
    items = db.scalars(
        select(VideoChapter)
        .where(VideoChapter.video_id == video.id)
        .order_by(VideoChapter.start_seconds.asc())
    ).all()
    return {"items": [_serialize(item) for item in items]}


@router.put("/{video_id}/chapters")
def replace_chapters(
    video_id: str,
    payload: ChapterReplace,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    video, is_owner = _chapter_access(db, video_id, user)
    if not is_owner:
        raise HTTPException(status_code=404, detail="Video not found.")
    if video.status not in {"ready", "published"}:
        raise HTTPException(status_code=409, detail="Complete the video upload before adding chapters.")

    items = payload.items
    starts = [item.start_seconds for item in items]
    if starts != sorted(starts) or len(starts) != len(set(starts)):
        raise HTTPException(status_code=422, detail="Chapter timestamps must be unique and in ascending order.")
    if items and items[0].start_seconds != 0:
        raise HTTPException(status_code=422, detail="The first chapter must start at 00:00.")
    if video.duration_seconds is not None and any(item.start_seconds >= video.duration_seconds for item in items):
        raise HTTPException(status_code=422, detail="Chapter timestamps must be inside the video duration.")

    db.query(VideoChapter).filter(VideoChapter.video_id == video.id).delete(synchronize_session=False)
    db.add_all([
        VideoChapter(
            video_id=video.id,
            title=item.title.strip(),
            start_seconds=item.start_seconds,
        )
        for item in items
    ])
    db.commit()

    saved = db.scalars(
        select(VideoChapter)
        .where(VideoChapter.video_id == video.id)
        .order_by(VideoChapter.start_seconds.asc())
    ).all()
    return {"video_id": video.id, "items": [_serialize(item) for item in saved]}
