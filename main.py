from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from api.v1.router import api_router
from config.settings import settings
from core.logging import configure_logging
from middleware.security import CSRFMiddleware
from webapp.pages import router as page_router

configure_logging()


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
app.include_router(page_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": settings.app_name}
