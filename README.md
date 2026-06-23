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
* Basic React frontend website check form
* Pytest coverage for URL normalization, SQLite storage, and API history behavior

Next planned milestone:

* Display saved check history in the React frontend

## Features

Currently implemented:

* `GET /api/health` endpoint for backend health checks

* `POST /api/check` endpoint for checking a website

* `GET /api/history` endpoint for viewing recent saved checks

* Optional history limit using `GET /api/history?limit=2`

* React frontend form for submitting website checks

* Frontend result card for availability, response time, DNS/IP details, redirect target, timestamp, and errors

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

The frontend will run at the URL shown by Vite, usually:

```text
http://127.0.0.1:5173
```

The backend must also be running at:

```text
http://127.0.0.1:8000
```

The website check form sends requests to:

```text
POST http://127.0.0.1:8000/api/check
```

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
6. UI polish and screenshots
7. Deployment documentation
