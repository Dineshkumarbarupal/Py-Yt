from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from config.settings import settings
from api.v1.router import api_router
from core.logging import configure_logging

configure_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema changes are applied through Alembic, never by implicit table creation here.
    yield

app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="asset"), name="static")
app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": settings.app_name}

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home():
    from pathlib import Path
    return HTMLResponse(Path("template/index.html").read_text(encoding="utf-8"))
