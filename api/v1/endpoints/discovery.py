from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/search")
async def search_videos(q: str = Query(min_length=1, max_length=200)):
    # Provider adapters and the local catalog repository will be connected in the next feature modules.
    return {
        "query": q,
        "items": [],
        "next_page_token": None,
        "status": "catalog_not_populated",
    }
