from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import storage
from app.checker import check_website


class WebsiteCheckRequest(BaseModel):
    url: str


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
    result = check_website(request.url)
    storage.save_check_result(result)
    return result


@app.get("/api/history")
def check_history(limit: int = Query(default=20, ge=1, le=100)):
    return storage.get_recent_checks(limit)
