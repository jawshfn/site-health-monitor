# Site Health Monitor

Site Health Monitor is a full-stack portfolio project for checking website availability, response time, and basic DNS/IP information.

## Project Status

In active development.

Current milestone completed:

* FastAPI backend scaffold
* Health check endpoint
* Website check endpoint
* URL normalization
* DNS/IP lookup
* HTTP status checking
* Response time measurement
* Basic pytest coverage for URL normalization

Next planned milestone:

* Add SQLite storage for website check history

## Features

Currently implemented:

* `GET /api/health` endpoint for backend health checks
* `POST /api/check` endpoint for checking a website
* Automatic URL normalization

  * `example.com` becomes `https://example.com`
  * `http://example.com` remains unchanged
* DNS/IP resolution using Python's `socket` module
* HTTP request checking using `httpx`
* Response time measurement in milliseconds
* Structured JSON response
* Network-free tests for URL normalization

Planned features:

* SQLite database storage for recent checks
* `GET /api/history` endpoint
* React frontend dashboard
* Website check form
* Result card UI
* History table
* Screenshots
* Deployment notes

## Tech Stack

Backend:

* Python
* FastAPI
* Pydantic
* httpx
* SQLite
* pytest

Frontend:

* React
* Vite
* JavaScript
* CSS

Development tools:

* Git
* GitHub
* VS Code

## Backend Setup

From the project root:

```powershell
cd backend
python -m venv .venv
```

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

FastAPI docs are available at:

```text
http://127.0.0.1:8000/docs
```

## Running Tests

From the `backend/` folder:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## API Examples

Health check:

```text
GET /api/health
```

Example response:

```json
{
  "status": "ok"
}
```

Website check:

```text
POST /api/check
```

Example request:

```json
{
  "url": "example.com"
}
```

Example response:

```json
{
  "input_url": "example.com",
  "normalized_url": "https://example.com",
  "hostname": "example.com",
  "status_code": 200,
  "is_up": true,
  "response_time_ms": 123,
  "ip_addresses": ["93.184.216.34"],
  "checked_at": "2026-06-23T12:00:00+00:00",
  "error": null
}
```

## Development Notes

This project is being built in small, focused commits. Each milestone adds one clear piece of functionality before moving to the next.

Milestone order:

1. Backend scaffold
2. Website check endpoint
3. SQLite history storage
4. React frontend scaffold
5. Frontend/backend integration
6. UI polish and screenshots
7. Deployment documentation
