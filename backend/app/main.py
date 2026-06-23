from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from urllib.parse import urlparse

from app import storage
from app.checker import check_website, normalize_url


class WebsiteCheckRequest(BaseModel):
    url: str


class SavedSiteRequest(BaseModel):
    url: str
    name: str | None = None


app = FastAPI(
    title="Site Health Monitor API",
    description="Backend API for checking website availability and response time.",
    version="0.1.0",
)

# Allows the future React frontend to call this backend during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Site Health Monitor API is running."
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok"
    }


@app.post("/api/check")
def check_site(request: WebsiteCheckRequest):
    return _check_and_save(request.url)


@app.get("/api/history")
def check_history(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items = storage.get_recent_checks(limit=limit, offset=offset)
    total = storage.count_check_history()

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(items) < total,
    }


@app.delete("/api/history")
def clear_history():
    deleted_count = storage.clear_check_history()
    return {
        "deleted": True,
        "deleted_count": deleted_count,
    }


@app.get("/api/sites")
def list_saved_sites():
    return storage.get_saved_sites()


@app.post("/api/sites/check-all")
def check_all_saved_sites():
    sites = storage.get_saved_sites()
    results = []

    for site in sites:
        check_result = _check_and_save(site["normalized_url"])
        results.append(
            {
                "site_id": site["id"],
                "name": site["name"],
                "url": site["url"],
                "normalized_url": site["normalized_url"],
                "hostname": site["hostname"],
                "is_up": check_result["is_up"],
                "status_code": check_result["status_code"],
                "response_time_ms": check_result["response_time_ms"],
                "error": check_result["error"],
                "checked_at": check_result["checked_at"],
            }
        )

    up_count = sum(1 for result in results if result["is_up"])

    return {
        "total": len(results),
        "up": up_count,
        "down": len(results) - up_count,
        "results": results,
    }


@app.post("/api/sites")
def create_saved_site(request: SavedSiteRequest):
    try:
        normalized_url = normalize_url(request.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    hostname = urlparse(normalized_url).hostname
    if hostname is None:
        raise HTTPException(status_code=400, detail="URL must include a valid hostname.")

    name = request.name.strip() if request.name else None
    return storage.create_saved_site(
        url=request.url,
        normalized_url=normalized_url,
        hostname=hostname,
        name=name or None,
    )


@app.delete("/api/sites/{site_id}")
def delete_saved_site(site_id: int):
    deleted_site = storage.delete_saved_site(site_id)

    if deleted_site is None:
        raise HTTPException(status_code=404, detail="Saved site not found.")

    return {
        "deleted": True,
        "site": deleted_site,
    }


def _check_and_save(url: str):
    result = check_website(url)
    storage.save_check_result(result)
    return result
