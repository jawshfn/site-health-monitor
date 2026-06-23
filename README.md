# Site Health Monitor

Site Health Monitor is a full-stack portfolio project for checking website availability, response time, and basic DNS/IP information.

The project is being built incrementally to demonstrate backend API development, database persistence, testing, frontend integration, and technical troubleshooting.

## Project Status

In active development.

Completed so far:

* FastAPI backend scaffold
* Health check endpoint
* Website check endpoint
* URL normalization
* DNS/IP lookup
* HTTP status checking
* Response time measurement
* SQLite-backed check history
* `GET /api/history` endpoint
* Clear Check History endpoint and frontend action
* Saved monitored sites/watchlist backend endpoints
* Backend check-all endpoint for saved monitored sites
* Basic React frontend website check form
* React frontend recent history display
* Polished React frontend layout for readability and responsiveness
* React frontend saved-sites/watchlist UI
* Frontend Check All Saved Sites button and dashboard summary
* Pytest coverage for URL normalization, SQLite storage, and API history behavior

Next planned milestone:

* Add screenshots to the README

## Features

Currently implemented:

* `GET /api/health` endpoint for backend health checks

* `POST /api/check` endpoint for checking a website

* `GET /api/history` endpoint for viewing recent saved checks

* `DELETE /api/history` endpoint for clearing saved check history without deleting saved monitored sites

* Optional history limit using `GET /api/history?limit=2`

* Saved monitored sites API

  * `GET /api/sites`
  * `POST /api/sites`
  * `POST /api/sites/check-all`
  * `DELETE /api/sites/{site_id}`

* Backend endpoint for checking every saved monitored site and storing each result in history

* React frontend form for submitting website checks

* React frontend saved-sites/watchlist UI for creating, checking, refreshing, and deleting monitored sites

* Frontend Check All Saved Sites button with total/up/down summary and per-site results

* Frontend result card for availability, response time, DNS/IP details, redirect target, timestamp, and errors

* Frontend recent history table loaded from `GET /api/history?limit=10`

* Frontend Clear History action with confirmation

* Refreshable saved check history after new website checks

* Polished responsive frontend layout with readable status badges, result summary cards, and mobile-friendly history display

* Automatic URL normalization

  * `example.com` becomes `https://example.com`
  * `http://example.com` remains unchanged

* DNS/IP resolution using Python's `socket` module

* HTTP request checking using `httpx`

* Response time measurement in milliseconds

* Final URL tracking after redirects

* SQLite storage for check history

* Structured JSON responses

* Network-free tests for URL normalization

* Temporary database tests for SQLite storage

* API endpoint tests with mocked website checks

Planned features:

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

## Frontend Setup

From the project root:

```powershell
cd frontend
npm install
```

Run the frontend dev server:

```powershell
npm run dev
```

The frontend will run at the URL shown by Vite, usually one of:

```text
http://127.0.0.1:5173
http://localhost:5173
```

The backend must also be running at:

```text
http://127.0.0.1:8000
```

The website check form sends requests to:

```text
POST http://127.0.0.1:8000/api/check
```

The recent history table loads saved checks from:

```text
GET http://127.0.0.1:8000/api/history?limit=10
```

The saved-sites/watchlist section loads monitored sites from:

```text
GET http://127.0.0.1:8000/api/sites
```

From the frontend, users can save monitored sites, delete saved sites, run a check for an individual saved site, and check all saved sites at once.

Build the frontend:

```powershell
npm run build
```

## Running Tests

From the `backend/` folder:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## API Examples

### Health check

```text
GET /api/health
```

Example response:

```json
{
  "status": "ok"
}
```

### Website check

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
  "final_url": "https://example.com",
  "hostname": "example.com",
  "status_code": 200,
  "is_up": true,
  "response_time_ms": 123,
  "ip_addresses": ["93.184.216.34"],
  "checked_at": "2026-06-23T12:00:00+00:00",
  "error": null
}
```

### Check history

```text
GET /api/history
```

Example response:

```json
[
  {
    "id": 2,
    "input_url": "https://github.com",
    "normalized_url": "https://github.com",
    "final_url": "https://github.com",
    "hostname": "github.com",
    "is_up": true,
    "status_code": 200,
    "response_time_ms": 428,
    "ip_addresses": ["140.82.112.3"],
    "error": null,
    "checked_at": "2026-06-23T17:35:08.709483+00:00"
  },
  {
    "id": 1,
    "input_url": "https://example.com",
    "normalized_url": "https://example.com",
    "final_url": "https://example.com",
    "hostname": "example.com",
    "is_up": true,
    "status_code": 200,
    "response_time_ms": 399,
    "ip_addresses": ["104.20.23.154", "172.66.147.243"],
    "error": null,
    "checked_at": "2026-06-23T17:34:17.589642+00:00"
  }
]
```

Limit the number of history results:

```text
GET /api/history?limit=2
```

Clear saved check history:

```text
DELETE /api/history
```

Example response:

```json
{
  "deleted": true,
  "deleted_count": 10
}
```

This only clears website check history. Saved monitored sites are not deleted.

### Saved monitored sites

```text
GET /api/sites
```

Example response:

```json
[
  {
    "id": 1,
    "name": "Example",
    "url": "example.com",
    "normalized_url": "https://example.com",
    "hostname": "example.com",
    "created_at": "2026-06-23T18:45:00.000000+00:00"
  }
]
```

```text
POST /api/sites
```

Example request:

```json
{
  "name": "Example",
  "url": "example.com"
}
```

Example response:

```json
{
  "id": 1,
  "name": "Example",
  "url": "example.com",
  "normalized_url": "https://example.com",
  "hostname": "example.com",
  "created_at": "2026-06-23T18:45:00.000000+00:00"
}
```

```text
DELETE /api/sites/1
```

Example response:

```json
{
  "deleted": true,
  "site": {
    "id": 1,
    "name": "Example",
    "url": "example.com",
    "normalized_url": "https://example.com",
    "hostname": "example.com",
    "created_at": "2026-06-23T18:45:00.000000+00:00"
  }
}
```

```text
POST /api/sites/check-all
```

Checks every saved monitored site, stores each result in check history, and returns a summary.

Example response:

```json
{
  "total": 2,
  "up": 1,
  "down": 1,
  "results": [
    {
      "site_id": 1,
      "name": "Example",
      "url": "example.com",
      "normalized_url": "https://example.com",
      "hostname": "example.com",
      "is_up": true,
      "status_code": 200,
      "response_time_ms": 123,
      "error": null,
      "checked_at": "2026-06-23T18:45:00.000000+00:00"
    },
    {
      "site_id": 2,
      "name": "Offline Example",
      "url": "offline.example",
      "normalized_url": "https://offline.example",
      "hostname": "offline.example",
      "is_up": false,
      "status_code": null,
      "response_time_ms": null,
      "error": "[Errno 11001] getaddrinfo failed",
      "checked_at": "2026-06-23T18:45:01.000000+00:00"
    }
  ]
}
```

## Local Data

Website check history is stored locally in a SQLite database.

SQLite database files are intentionally ignored by git so local check history is not committed to the repository.

Ignored database file types include:

```text
*.db
*.sqlite
*.sqlite3
```

## Development Notes

This project is being built in small, focused commits. Each milestone adds one clear piece of functionality before moving to the next.

Milestone order:

1. Backend scaffold
2. Website check endpoint
3. SQLite history storage
4. React frontend website check form
5. Frontend history display
6. UI polish
7. Backend saved-sites/watchlist API
8. Frontend saved-sites/watchlist UI
9. Backend check-all saved sites API
10. Frontend Check All Saved Sites button and dashboard summary
11. Clear Check History
12. Screenshots
13. Deployment documentation
