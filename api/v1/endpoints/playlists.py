from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.models import Playlist, PlaylistItem, User, Video
from db.session import get_db
from core.dependencies import get_current_user

router = APIRouter(prefix="/playlists")

class PlaylistCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=5000)
    visibility: str = Field(default="private", pattern="^(public|unlisted|private)$")

class PlaylistItemCreate(BaseModel):
    video_id: str

@router.get("/mine")
def my_playlists(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": db.scalars(select(Playlist).where(Playlist.owner_id == user.id).order_by(Playlist.created_at.desc())).all()}

@router.post("", status_code=201)
def create_playlist(payload: PlaylistCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    playlist = Playlist(owner_id=user.id, title=payload.title.strip(), description=payload.description.strip(), visibility=payload.visibility)
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    return playlist

@router.post("/{playlist_id}/items", status_code=201)
def add_item(playlist_id: str, payload: PlaylistItemCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    playlist = db.get(Playlist, playlist_id)
    video = db.get(Video, payload.video_id)
    if not playlist or playlist.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Playlist not found.")
    if not video or (video.visibility == "private" and video.channel_id != playlist.owner_id):
        raise HTTPException(status_code=404, detail="Video not found.")
    count = db.scalar(select(PlaylistItem).where(PlaylistItem.playlist_id == playlist_id))
    item = PlaylistItem(playlist_id=playlist_id, video_id=video.id, position=0 if count is None else 1)
    db.add(item)
    db.commit()
    return {"status": "added", "playlist_id": playlist_id, "video_id": video.id}
