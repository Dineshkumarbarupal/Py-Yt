from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from botocore.exceptions import BotoCoreError, ClientError
from config.settings import settings
from core.dependencies import get_current_user
from core.media_storage import MediaStorageNotConfigured, create_upload_form, inspect_uploaded_object
from db.models import Channel, Video, User, new_id
from db.session import get_db

router = APIRouter(prefix="/uploads")

ALLOWED_VIDEO_TYPES = {
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/quicktime": "mov",
}

class UploadRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    category: str = Field(default="General", pattern="^(General|Music|Gaming|Technology|Learning|Live|Comedy|Sports|News|Entertainment)$")
    content_type: str
    file_size_bytes: int = Field(gt=0)

@router.post("/presign", status_code=201)
def presign_upload(payload: UploadRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=415, detail="Supported formats are MP4, WebM and QuickTime video.")
    if payload.file_size_bytes > settings.upload_max_bytes:
        raise HTTPException(status_code=413, detail=f"Video exceeds the configured {settings.upload_max_bytes} byte upload limit.")
    channel = db.scalar(select(Channel).where(Channel.owner_id == user.id))
    if not channel:
        raise HTTPException(status_code=404, detail="Create a channel before uploading a video.")

    video_id = new_id()
    object_key = f"videos/{channel.id}/{video_id}.{ALLOWED_VIDEO_TYPES[payload.content_type]}"
    video = Video(
        id=video_id,
        channel_id=channel.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        category=payload.category,
        storage_key=object_key,
        mime_type=payload.content_type,
        file_size_bytes=payload.file_size_bytes,
        source_type="upload",
        visibility="private",
        status="uploading",
    )
    db.add(video)
    try:
        form = create_upload_form(object_key, payload.content_type, payload.file_size_bytes)
        db.commit()
    except MediaStorageNotConfigured as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc))
    except (BotoCoreError, ClientError):
        db.rollback()
        raise HTTPException(status_code=502, detail="Could not prepare the upload with the media storage provider.")
    return {
        "video_id": video_id,
        "upload_url": form["url"],
        "fields": form["fields"],
        "expires_in": 900,
        "max_file_size_bytes": settings.upload_max_bytes,
    }

@router.post("/{video_id}/complete")
def complete_upload(video_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    video = db.get(Video, video_id)
    channel = db.scalar(select(Channel).where(Channel.owner_id == user.id))
    if not video or not channel or video.channel_id != channel.id:
        raise HTTPException(status_code=404, detail="Upload not found.")
    if video.status != "uploading" or not video.storage_key:
        raise HTTPException(status_code=409, detail="This upload is not awaiting completion.")
    try:
        metadata = inspect_uploaded_object(video.storage_key)
    except MediaStorageNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (BotoCoreError, ClientError):
        raise HTTPException(status_code=409, detail="The uploaded object was not found. Retry the upload.")
    if metadata.get("ContentLength") != video.file_size_bytes or metadata.get("ContentType") != video.mime_type:
        raise HTTPException(status_code=422, detail="Uploaded file metadata does not match the authorized upload.")
    video.status = "ready"
    db.commit()
    return {"video_id": video.id, "status": video.status, "message": "Upload verified. You can now publish the video."}
