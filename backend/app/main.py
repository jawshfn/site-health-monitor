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


class SavedSiteNameUpdateRequest(BaseModel):
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


@app.get("/api/summary")
def dashboard_summary():
    return storage.get_dashboard_summary()


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
                "status_label": check_result.get("status_label"),
                "failure_type": check_result.get("failure_type"),
                "failure_stage": check_result.get("failure_stage"),
                "dns_status": check_result.get("dns_status"),
                "connection_status": check_result.get("connection_status"),
                "http_status": check_result.get("http_status"),
                "diagnostic_summary": check_result.get("diagnostic_summary"),
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
    try:
        return storage.create_saved_site(
            url=request.url,
            normalized_url=normalized_url,
            hostname=hostname,
            name=name or None,
        )
    except storage.DuplicateSavedSiteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.delete("/api/sites/{site_id}")
def delete_saved_site(site_id: int):
    deleted_site = storage.delete_saved_site(site_id)

    if deleted_site is None:
        raise HTTPException(status_code=404, detail="Saved site not found.")

    return {
        "deleted": True,
        "site": deleted_site,
    }


@app.patch("/api/sites/{site_id}")
def update_saved_site_name(site_id: int, request: SavedSiteNameUpdateRequest):
    name = request.name.strip() if request.name else None
    updated_site = storage.update_saved_site_name(site_id, name or None)

    if updated_site is None:
        raise HTTPException(status_code=404, detail="Saved site not found.")

    return updated_site


def _check_and_save(url: str):
    result = check_website(url)
    _add_status_defaults(result)
    storage.save_check_result(result)
    return result


def _add_status_defaults(result: dict):
    is_up = bool(result.get("is_up"))
    result.setdefault("status_label", "healthy" if is_up else "unknown_error")
    result.setdefault("failure_type", None if is_up else "unknown_error")
    result.setdefault("failure_stage", None if is_up else "unknown")
    result.setdefault("dns_status", "not_checked")
    result.setdefault("connection_status", "not_checked")
    result.setdefault("http_status", "not_attempted")
    result.setdefault(
        "diagnostic_summary",
        "The check completed successfully."
        if is_up
        else "This checker observed an issue with the request.",
    )
