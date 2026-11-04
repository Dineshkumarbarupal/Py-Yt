from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from db.models import Channel, Playlist, PlaylistItem, User, Video
from db.session import get_db
from core.dependencies import get_current_user, get_optional_user

router = APIRouter(prefix="/playlists")

class PlaylistCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=5000)
    visibility: str = Field(default="private", pattern="^(public|unlisted|private)$")

class PlaylistItemCreate(BaseModel):
    video_id: str

@router.get("/mine")
def my_playlists(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.scalars(
        select(Playlist).where(Playlist.owner_id == user.id).order_by(Playlist.created_at.desc())
    ).all()
    return {"items": items}

@router.post("", status_code=201)
def create_playlist(payload: PlaylistCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    playlist = Playlist(
        owner_id=user.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        visibility=payload.visibility,
    )
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    return playlist

@router.get("/{playlist_id}")
def get_playlist(playlist_id: str, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    playlist = db.get(Playlist, playlist_id)
    if not playlist or (playlist.visibility == "private" and (not user or playlist.owner_id != user.id)):
        raise HTTPException(status_code=404, detail="Playlist not found.")
    rows = db.execute(
        select(PlaylistItem, Video)
        .join(Video, PlaylistItem.video_id == Video.id)
        .where(PlaylistItem.playlist_id == playlist_id)
        .order_by(PlaylistItem.position.asc())
    ).all()
    return {
        "id": playlist.id,
        "title": playlist.title,
        "description": playlist.description,
        "items": [{"position": item.position, "video_id": video.id, "title": video.title} for item, video in rows],
    }

@router.post("/{playlist_id}/items", status_code=201)
def add_item(playlist_id: str, payload: PlaylistItemCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    playlist = db.get(Playlist, playlist_id)
    video = db.get(Video, payload.video_id)
    if not playlist or playlist.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Playlist not found.")
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")
    video_channel = db.get(Channel, video.channel_id)
    is_owner = bool(video_channel and video_channel.owner_id == user.id)
    if not is_owner and (video.visibility != "public" or video.status != "published"):
        raise HTTPException(status_code=404, detail="Video not found.")
    existing = db.scalar(
        select(PlaylistItem).where(
            PlaylistItem.playlist_id == playlist_id,
            PlaylistItem.video_id == video.id,
        )
    )
    if existing:
        return {"status": "already_added", "playlist_id": playlist_id, "video_id": video.id}
    next_position = db.scalar(
        select(func.coalesce(func.max(PlaylistItem.position), -1)).where(PlaylistItem.playlist_id == playlist_id)
    ) + 1
    db.add(PlaylistItem(playlist_id=playlist_id, video_id=video.id, position=next_position))
    db.commit()
    return {"status": "added", "playlist_id": playlist_id, "video_id": video.id, "position": next_position}
