from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session
from db.models import Channel, Video

def serialize_public_video(video: Video, channel: Channel) -> dict:
    return {
        "id": video.id,
        "title": video.title,
        "category": video.category,
        "video_format": video.video_format,
        "thumbnail_url": video.thumbnail_url,
        "duration_seconds": video.duration_seconds,
        "view_count": video.view_count,
        "channel_name": channel.name,
        "channel_handle": channel.handle,
        "published_at": video.published_at,
    }

def public_feed(
    db: Session,
    category: str | None = None,
    limit: int = 24,
) -> list[dict]:
    statement = (
        select(Video, Channel)
        .join(Channel, Video.channel_id == Channel.id)
        .where(Video.status == "published", Video.visibility == "public")
    )
    if category and category != "All":
        statement = statement.where(Video.category == category)
    rows = db.execute(
        statement.order_by(desc(Video.published_at), desc(Video.created_at)).limit(limit)
    ).all()
    return [serialize_public_video(video, channel) for video, channel in rows]

def search_public_videos(
    db: Session,
    query: str,
    category: str | None = None,
    limit: int = 24,
    offset: int = 0,
) -> list[dict]:
    pattern = f"%{query.strip()}%"
    statement = (
        select(Video, Channel)
        .join(Channel, Video.channel_id == Channel.id)
        .where(
            Video.status == "published",
            Video.visibility == "public",
            or_(Video.title.ilike(pattern), Video.description.ilike(pattern), Channel.name.ilike(pattern)),
        )
    )
    if category and category != "All":
        statement = statement.where(Video.category == category)
    rows = db.execute(
        statement.order_by(desc(Video.published_at), desc(Video.created_at)).offset(offset).limit(limit)
    ).all()
    return [serialize_public_video(video, channel) for video, channel in rows]


def public_shorts(db: Session, limit: int = 20, offset: int = 0) -> list[dict]:
    rows = db.execute(
        select(Video, Channel)
        .join(Channel, Video.channel_id == Channel.id)
        .where(
            Video.status == "published",
            Video.visibility == "public",
            Video.video_format == "short",
        )
        .order_by(desc(Video.published_at), desc(Video.created_at))
        .offset(offset)
        .limit(limit)
    ).all()
    return [serialize_public_video(video, channel) for video, channel in rows]


def search_suggestions(db: Session, query: str, limit: int = 8) -> list[dict]:
    normalized = query.strip()
    if len(normalized) < 2:
        return []
    pattern = f"%{normalized}%"
    video_titles = db.scalars(
        select(Video.title)
        .where(
            Video.status == "published",
            Video.visibility == "public",
            Video.title.ilike(pattern),
        )
        .group_by(Video.title)
        .order_by(func.max(Video.published_at).desc())
        .limit(limit)
    ).all()
    channel_names = db.scalars(
        select(Channel.name)
        .join(Video, Video.channel_id == Channel.id)
        .where(
            Video.status == "published",
            Video.visibility == "public",
            Channel.name.ilike(pattern),
        )
        .group_by(Channel.name)
        .order_by(func.max(Video.published_at).desc())
        .limit(limit)
    ).all()
    suggestions = [{"label": title, "kind": "video"} for title in video_titles]
    suggestions.extend({"label": name, "kind": "channel"} for name in channel_names)
    seen = set()
    unique = []
    for item in suggestions:
        key = item["label"].casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique[:limit]
