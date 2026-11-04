from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import desc, select
from config.settings import settings
from api.v1.router import api_router
from core.logging import configure_logging
from db.models import Channel, User, Video
from core.dependencies import get_optional_user
from db.session import SessionLocal
from middleware.security import CSRFMiddleware

configure_logging()
templates = Jinja2Templates(directory="template")
templates.env.loader = ChoiceLoader([FileSystemLoader("template"), FileSystemLoader(".")])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run Alembic migrations as a controlled deployment/release step, not on every worker startup.
    yield

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
)
app.add_middleware(CSRFMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.mount("/assets", StaticFiles(directory="asset"), name="assets")
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js")
app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": settings.app_name}

@app.get("/", include_in_schema=False)
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
    return templates.TemplateResponse(request=request, name="index.html", context={"videos": videos})

@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})

@app.get("/signup", include_in_schema=False)
async def signup_page(request: Request):
    return templates.TemplateResponse(request=request, name="signup.html", context={})

@app.get("/studio", include_in_schema=False)
async def studio_page(request: Request):
    return templates.TemplateResponse(request=request, name="studio.html", context={})

@app.get("/studio/upload", include_in_schema=False)
async def studio_upload_page(request: Request):
    return templates.TemplateResponse(request=request, name="studio_upload.html", context={})

@app.get("/studio/{studio_section}", include_in_schema=False)
async def studio_section_page(request: Request, studio_section: str):
    studio_sections = {
        "content": ("Your content", "Review draft and published videos in the Creator Studio."),
        "analytics": ("Channel analytics", "Views, watch time, audience and revenue analytics are planned for a later phase."),
        "comments": ("Comments", "Comment review and moderation tools are planned for a later phase."),
    }
    if studio_section not in studio_sections:
        return JSONResponse({"detail": "Not found."}, status_code=404)
    page_templates = {
        "content": "studio_content.html",
        "analytics": "studio_analytics.html",
        "comments": "studio_comments.html",
    }
    if studio_section in page_templates:
        return templates.TemplateResponse(
            request=request,
            name=page_templates[studio_section],
            context={},
        )
    title, description = studio_sections[studio_section]
    return templates.TemplateResponse(request=request, name="section.html", context={"title": title, "description": description})

@app.get("/playlist/{playlist_id}", include_in_schema=False)
async def playlist_detail_page(request: Request, playlist_id: str):
    return templates.TemplateResponse(
        request=request,
        name="playlist_detail.html",
        context={"playlist_id": playlist_id},
    )

@app.get("/watch/{video_id}", include_in_schema=False)
async def watch_page(request: Request, video_id: str, user: User | None = Depends(get_optional_user)):
    with SessionLocal() as db:
        row = db.execute(
            select(Video, Channel)
            .join(Channel, Video.channel_id == Channel.id)
            .where(Video.id == video_id, Video.status.in_(["ready", "published"]))
        ).first()
    if not row:
        return templates.TemplateResponse(request=request, name="section.html", status_code=404, context={
            "title": "Video unavailable",
            "description": "This video does not exist or is not available.",
        })
    video, channel = row
    if video.status != "published" and not (user and user.id == channel.owner_id):
        return templates.TemplateResponse(request=request, name="section.html", status_code=404, context={
            "title": "Video unavailable",
            "description": "This video does not exist or is not available.",
        })
    if video.visibility == "private" and not (user and user.id == channel.owner_id):
        return templates.TemplateResponse(request=request, name="section.html", status_code=404, context={
            "title": "Video unavailable",
            "description": "This video does not exist or is not available.",
        })
    return templates.TemplateResponse(request=request, name="watch.html", context={"video": video, "channel": channel})

@app.get("/@{handle}", include_in_schema=False)
async def public_channel_page(request: Request, handle: str):
    with SessionLocal() as db:
        channel = db.scalar(select(Channel).where(Channel.handle == handle))
        if not channel:
            return templates.TemplateResponse(request=request, name="section.html", status_code=404, context={
                "title": "Channel not found",
                "description": "This channel does not exist or is unavailable.",
            })
        rows = db.execute(
            select(Video, Channel)
            .join(Channel, Video.channel_id == Channel.id)
            .where(Channel.id == channel.id, Video.status == "published", Video.visibility == "public")
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

@app.get("/channel", include_in_schema=False)
async def own_channel(request: Request, user: User | None = Depends(get_optional_user)):
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=303)
    with SessionLocal() as db:
        channel = db.scalar(select(Channel).where(Channel.owner_id == user.id))
    if not channel:
        return templates.TemplateResponse(request=request, name="section.html", status_code=404, context={
            "title": "Channel not found",
            "description": "Your channel has not been created yet.",
        })
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/@{channel.handle}", status_code=303)

@app.get("/{section}", include_in_schema=False)
async def section_page(request: Request, section: str):
    sections = {
        "channel": ("Your channel", "Your public channel profile and videos will appear here."),
        "shorts": ("Shorts", "Vertical short-form video discovery will be enabled with the media pipeline."),
        "subscriptions": ("Subscriptions", "Sign in and subscribe to channels to build your feed."),
        "history": ("History", "Your watch history will appear here when watch tracking is enabled."),
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
    if section == "subscriptions":
        return templates.TemplateResponse(request=request, name="subscriptions.html", context={})
    if section == "playlists":
        return templates.TemplateResponse(request=request, name="playlists.html", context={})
    if section not in sections:
        return JSONResponse({"detail": "Not found."}, status_code=404)
    title, description = sections[section]
    return templates.TemplateResponse(request=request, name="section.html", context={"title": title, "description": description})
