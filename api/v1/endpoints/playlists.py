from fastapi import APIRouter, Depends, HTTPException, Response
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

class PlaylistUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    visibility: str | None = Field(default=None, pattern="^(public|unlisted|private)$")

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
    is_owner = bool(user and playlist.owner_id == user.id)
    statement = (
        select(PlaylistItem, Video)
        .join(Video, PlaylistItem.video_id == Video.id)
        .where(PlaylistItem.playlist_id == playlist_id, Video.status != "deleted")
        .order_by(PlaylistItem.position.asc())
    )
    if not is_owner:
        statement = statement.where(Video.status == "published", Video.visibility == "public")
    rows = db.execute(statement).all()
    return {
        "id": playlist.id,
        "title": playlist.title,
        "description": playlist.description,
        "items": [
            {"position": item.position, "video_id": video.id, "title": video.title}
            for item, video in rows
        ],
    }


@router.patch("/{playlist_id}")
def update_playlist(
    playlist_id: str,
    payload: PlaylistUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    playlist = db.get(Playlist, playlist_id)
    if not playlist or playlist.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Playlist not found.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(playlist, key, value.strip() if isinstance(value, str) and key in {"title", "description"} else value)
    db.commit()
    db.refresh(playlist)
    return playlist

@router.delete("/{playlist_id}", status_code=204)
def delete_playlist(
    playlist_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    playlist = db.get(Playlist, playlist_id)
    if not playlist or playlist.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Playlist not found.")
    db.delete(playlist)
    db.commit()
    return Response(status_code=204)

@router.post("/{playlist_id}/items", status_code=201)
def add_item(playlist_id: str, payload: PlaylistItemCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    playlist = db.get(Playlist, playlist_id)
    video = db.get(Video, payload.video_id)
    if not playlist or playlist.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Playlist not found.")
    if not video or video.status == "deleted":
        raise HTTPException(status_code=404, detail="Video not found.")
    video_channel = db.get(Channel, video.channel_id)
    is_video_owner = bool(video_channel and video_channel.owner_id == user.id)
    is_public_video = video.visibility == "public" and video.status == "published"
    if not is_public_video and not (is_video_owner and playlist.visibility == "private"):
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

@router.delete("/{playlist_id}/items/{video_id}", status_code=204)
def remove_item(
    playlist_id: str,
    video_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    playlist = db.get(Playlist, playlist_id)
    if not playlist or playlist.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Playlist not found.")
    item = db.scalar(
        select(PlaylistItem).where(
            PlaylistItem.playlist_id == playlist_id,
            PlaylistItem.video_id == video_id,
        )
    )
    if item:
        db.delete(item)
        db.commit()
    return Response(status_code=204)
