from fastapi import APIRouter
from sqlalchemy import text
from db.session import engine

router = APIRouter()

@router.get("/ready")
async def ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready", "database": "available"}
    except Exception:
        return {"status": "degraded", "database": "unavailable"}
