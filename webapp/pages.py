from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader
from sqlalchemy import desc, select

from core.dependencies import get_optional_user
from db.models import Channel, User, Video
from db.session import SessionLocal

router = APIRouter()
templates = Jinja2Templates(directory="template")
templates.env.loader = ChoiceLoader(
    [FileSystemLoader("template"), FileSystemLoader(".")]
)


@router.get("/", include_in_schema=False)
async def home(request: Request):
    with SessionLocal() as db:
        rows = db.execute(
            select(Video, Channel)
            .join(Channel, Video.channel_id == Channel.id)
            .where(Video.status == "published", Video.visibility == "public")
            .order_by(desc(Video.published_at), desc(Video.created_at))
            .limit(24)
        ).all()
        videos = [
            {
                "id": video.id,
                "title": video.title,
                "thumbnail_url": video.thumbnail_url,
                "duration": None,
                "channel_name": channel.name,
                "channel_initial": channel.name[:1].upper(),
                "view_label": f"{video.view_count:,} views",
                "published_label": video.published_at.strftime("%b %d, %Y") if video.published_at else "",
            }
            for video, channel in rows
        ]
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"videos": videos},
    )


@router.get("/admin/moderation", include_in_schema=False)
async def admin_moderation_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin_moderation.html",
        context={},
    )


@router.get("/shorts", include_in_schema=False)
async def shorts_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="shorts.html",
        context={},
    )


@router.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


@router.get("/signup", include_in_schema=False)
async def signup_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="signup.html",
        context={},
    )


@router.get("/studio", include_in_schema=False)
async def studio_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="studio.html",
        context={},
    )


@router.get("/studio/upload", include_in_schema=False)
async def studio_upload_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="studio_upload.html",
        context={},
    )


@router.get("/studio/{studio_section}", include_in_schema=False)
async def studio_section_page(request: Request, studio_section: str):
    page_templates = {
        "content": "studio_content.html",
        "analytics": "studio_analytics.html",
        "comments": "studio_comments.html",
    }
    if studio_section not in page_templates:
        return JSONResponse({"detail": "Not found."}, status_code=404)
    return templates.TemplateResponse(
        request=request,
        name=page_templates[studio_section],
        context={},
    )


@router.get("/playlist/{playlist_id}", include_in_schema=False)
async def playlist_detail_page(request: Request, playlist_id: str):
    return templates.TemplateResponse(
        request=request,
        name="playlist_detail.html",
        context={"playlist_id": playlist_id},
    )


@router.get("/watch/{video_id}", include_in_schema=False)
async def watch_page(
    request: Request,
    video_id: str,
    user: User | None = Depends(get_optional_user),
):
    with SessionLocal() as db:
        row = db.execute(
            select(Video, Channel)
            .join(Channel, Video.channel_id == Channel.id)
            .where(Video.id == video_id, Video.status.in_(["ready", "published"]))
        ).first()
    if not row:
        return templates.TemplateResponse(
            request=request,
            name="section.html",
            status_code=404,
            context={
                "title": "Video unavailable",
                "description": "This video does not exist or is not available.",
            },
        )
    video, channel = row
    if video.status != "published" and not (user and user.id == channel.owner_id):
        return templates.TemplateResponse(
            request=request,
            name="section.html",
            status_code=404,
            context={
                "title": "Video unavailable",
                "description": "This video does not exist or is not available.",
            },
        )
    if video.visibility == "private" and not (user and user.id == channel.owner_id):
        return templates.TemplateResponse(
            request=request,
            name="section.html",
            status_code=404,
            context={
                "title": "Video unavailable",
                "description": "This video does not exist or is not available.",
            },
        )
    return templates.TemplateResponse(
        request=request,
        name="watch.html",
        context={"video": video, "channel": channel},
    )


@router.get("/@{handle}", include_in_schema=False)
async def public_channel_page(request: Request, handle: str):
    with SessionLocal() as db:
        channel = db.scalar(select(Channel).where(Channel.handle == handle))
        if not channel:
            return templates.TemplateResponse(
                request=request,
                name="section.html",
                status_code=404,
                context={
                    "title": "Channel not found",
                    "description": "This channel does not exist or is unavailable.",
                },
            )
        rows = db.execute(
            select(Video, Channel)
            .join(Channel, Video.channel_id == Channel.id)
            .where(
                Channel.id == channel.id,
                Video.status == "published",
                Video.visibility == "public",
            )
            .order_by(desc(Video.published_at), desc(Video.created_at))
            .limit(48)
        ).all()
        videos = [
            {
                "id": video.id,
                "title": video.title,
                "thumbnail_url": video.thumbnail_url,
                "duration": None,
                "channel_name": channel.name,
                "channel_initial": channel.name[:1].upper(),
                "view_label": f"{video.view_count:,} views",
                "published_label": video.published_at.strftime("%b %d, %Y") if video.published_at else "",
            }
            for video, _channel in rows
        ]
    return templates.TemplateResponse(
        request=request,
        name="channel.html",
        context={"channel": channel, "videos": videos},
    )


@router.get("/account", include_in_schema=False)
async def account_page():
    return RedirectResponse(url="/settings", status_code=303)


@router.get("/channel", include_in_schema=False)
async def own_channel(
    user: User | None = Depends(get_optional_user),
):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    with SessionLocal() as db:
        channel = db.scalar(select(Channel).where(Channel.owner_id == user.id))
    if not channel:
        return JSONResponse(
            {"detail": "Your channel has not been created yet."},
            status_code=404,
        )
    return RedirectResponse(url=f"/@{channel.handle}", status_code=303)


@router.get("/{section}", include_in_schema=False)
async def section_page(request: Request, section: str):
    sections = {
        "channel": ("Your channel", "Your public channel profile and videos will appear here."),
        "shorts": ("Shorts", "Vertical short-form video discovery is available in the Shorts feed."),
        "subscriptions": ("Subscriptions", "Sign in and subscribe to channels to build your feed."),
        "history": ("History", "Your watch history is available in your library."),
        "playlists": ("Playlists", "Create and organize playlists from your library."),
        "watch-later": ("Watch later", "Save videos to watch them later."),
        "liked": ("Liked videos", "Videos you have liked will appear here."),
        "settings": ("Settings", "Manage profile, privacy, notifications and playback preferences."),
        "account": ("Your account", "Sign in to manage your Py-Yt account."),
        "notifications": ("Notifications", "Creator and channel updates will appear here."),
        "help": ("Help & feedback", "Help documentation and feedback tools are being prepared."),
    }
    if section in {"watch-later", "liked", "history"}:
        title, _description = sections[section]
        return templates.TemplateResponse(
            request=request,
            name="library.html",
            context={"title": title, "library_key": section},
        )
    page_templates = {
        "subscriptions": "subscriptions.html",
        "playlists": "playlists.html",
        "settings": "settings.html",
        "notifications": "notifications.html",
    }
    if section in page_templates:
        return templates.TemplateResponse(
            request=request,
            name=page_templates[section],
            context={},
        )
    if section not in sections:
        return JSONResponse({"detail": "Not found."}, status_code=404)
    title, description = sections[section]
    return templates.TemplateResponse(
        request=request,
        name="section.html",
        context={"title": title, "description": description},
    )
