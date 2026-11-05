import re

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from starlette.responses import PlainTextResponse

from core.dependencies import get_current_user, get_optional_user
from db.models import Channel, User, Video, VideoCaption
from db.session import get_db

router = APIRouter(prefix="/videos")

LANGUAGE_PATTERN = r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$"
VTT_CUE_TIMING = re.compile(
    r"(?m)^(?:[0-9]{2}:)?[0-9]{2}:[0-9]{2}\.[0-9]{3}\s+-->\s+"
    r"(?:[0-9]{2}:)?[0-9]{2}:[0-9]{2}\.[0-9]{3}(?:\s+.*)?$"
)
MAX_VTT_CHARS = 1_000_000


class CaptionUpsert(BaseModel):
    language: str = Field(min_length=2, max_length=20, pattern=LANGUAGE_PATTERN)
    label: str = Field(min_length=1, max_length=80)
    vtt_content: str = Field(min_length=1, max_length=MAX_VTT_CHARS)
    is_default: bool = False

    @model_validator(mode="after")
    def validate_non_blank_labels(self):
        if not self.language.strip():
            raise ValueError("Language code cannot be blank.")
        if not self.label.strip():
            raise ValueError("Caption label cannot be blank.")
        return self


def _video_access(
    db: Session,
    video_id: str,
    user: User | None,
) -> tuple[Video, bool]:
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")
    channel = db.get(Channel, video.channel_id)
    is_owner = bool(user and channel and channel.owner_id == user.id)
    if not is_owner and not (
        video.status == "published" and video.visibility in {"public", "unlisted"}
    ):
        raise HTTPException(status_code=404, detail="Video not found.")
    if video.status == "deleted" or video.status == "removed":
        raise HTTPException(status_code=404, detail="Video not found.")
    return video, is_owner


def _serialize_caption(caption: VideoCaption, video_id: str) -> dict:
    return {
        "id": caption.id,
        "language": caption.language,
        "label": caption.label,
        "is_default": caption.is_default,
        "vtt_url": f"/api/v1/videos/{video_id}/captions/{caption.id}/vtt",
        "created_at": caption.created_at,
    }


def _validated_vtt(raw_content: str) -> str:
    normalized = raw_content.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff").strip()
    lines = normalized.splitlines()
    if not lines or not (
        lines[0] == "WEBVTT" or lines[0].startswith("WEBVTT ")
    ):
        raise HTTPException(status_code=422, detail="Caption file must begin with a WEBVTT header.")
    if "\x00" in normalized or not VTT_CUE_TIMING.search(normalized):
        raise HTTPException(status_code=422, detail="Caption file must contain at least one valid WebVTT cue.")
    if len(normalized) > MAX_VTT_CHARS:
        raise HTTPException(status_code=413, detail="Caption file exceeds the 1 MB limit.")
    return normalized + "\n"


@router.get("/{video_id}/captions")
def list_captions(
    video_id: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    video, _is_owner = _video_access(db, video_id, user)
    captions = db.scalars(
        select(VideoCaption)
        .where(VideoCaption.video_id == video.id)
        .order_by(VideoCaption.is_default.desc(), VideoCaption.language.asc())
    ).all()
    return {"items": [_serialize_caption(caption, video.id) for caption in captions]}


@router.put("/{video_id}/captions")
def upsert_caption(
    video_id: str,
    payload: CaptionUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    video, is_owner = _video_access(db, video_id, user)
    if not is_owner:
        raise HTTPException(status_code=404, detail="Video not found.")
    if video.status not in {"ready", "published"}:
        raise HTTPException(status_code=409, detail="Complete the video upload before adding captions.")

    normalized_content = _validated_vtt(payload.vtt_content)
    language = payload.language.strip()
    caption = db.scalar(
        select(VideoCaption).where(
            VideoCaption.video_id == video.id,
            VideoCaption.language == language,
        )
    )
    if payload.is_default:
        db.execute(
            update(VideoCaption)
            .where(VideoCaption.video_id == video.id)
            .values(is_default=False)
        )

    if caption:
        caption.label = payload.label.strip()
        caption.vtt_content = normalized_content
        caption.is_default = payload.is_default
    else:
        caption = VideoCaption(
            video_id=video.id,
            language=language,
            label=payload.label.strip(),
            vtt_content=normalized_content,
            is_default=payload.is_default,
        )
        db.add(caption)

    db.commit()
    db.refresh(caption)
    return _serialize_caption(caption, video.id)


@router.delete("/{video_id}/captions/{caption_id}", status_code=204)
def delete_caption(
    video_id: str,
    caption_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    video, is_owner = _video_access(db, video_id, user)
    if not is_owner:
        raise HTTPException(status_code=404, detail="Video not found.")
    caption = db.scalar(
        select(VideoCaption).where(
            VideoCaption.id == caption_id,
            VideoCaption.video_id == video.id,
        )
    )
    if caption:
        db.delete(caption)
        db.commit()
    return Response(status_code=204)


@router.get("/{video_id}/captions/{caption_id}/vtt")
def get_caption_file(
    video_id: str,
    caption_id: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    video, is_owner = _video_access(db, video_id, user)
    caption = db.scalar(
        select(VideoCaption).where(
            VideoCaption.id == caption_id,
            VideoCaption.video_id == video.id,
        )
    )
    if not caption:
        raise HTTPException(status_code=404, detail="Caption track not found.")
    cache_control = "private, max-age=60" if is_owner else "public, max-age=300"
    return PlainTextResponse(
        caption.vtt_content,
        media_type="text/vtt",
        headers={"Cache-Control": cache_control, "X-Content-Type-Options": "nosniff"},
    )
