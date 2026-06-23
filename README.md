# Site Health Monitor

Site Health Monitor is a full-stack web app for checking website availability from a local HTTP checker, including response time, redirects, observed result type, and DNS/IP information. Users can run one-time checks, save monitored sites, check all saved sites at once, and review saved check history through a React dashboard backed by a FastAPI API and SQLite storage.

## Screenshots

Screenshots coming soon.

## Features

* Check website availability, HTTP status, response time, redirects, and DNS/IP information
* Classify observed results as healthy, HTTP error, timeout, DNS failure, connection failure, invalid URL, or unknown error
* View dashboard summary cards for saved sites, total checks, latest healthy/issues counts, and average response time
* Automatically normalize URLs, such as converting `example.com` to `https://example.com`
* Save monitored sites in a local watchlist
* Prevent duplicate saved sites using normalized URLs
* Edit saved-site friendly names
* Check individual saved sites or check all saved sites at once
* Store check history in SQLite
* Browse older history with Load More pagination
* Clear check history without deleting saved monitored sites
* Responsive React frontend with observed-result badges, result cards, and mobile-friendly history display
* Backend tests for URL normalization, storage behavior, API endpoints, saved sites, history pagination, and check-all behavior

## Tech Stack

**Backend**

* Python
* FastAPI
* Pydantic
* httpx
* SQLite
* pytest

**Frontend**

* React
* Vite
* JavaScript
* CSS

## Quick Start

### Backend

From the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

FastAPI docs are available at:

```text
http://127.0.0.1:8000/docs
```

### Frontend

Open a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at the URL shown by Vite, usually:

```text
http://127.0.0.1:5173
```

## Running Tests

From the `backend/` folder:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Build the frontend:

```powershell
cd frontend
npm run build
```

## API Overview

| Method   | Endpoint                         | Description                                      |
| -------- | -------------------------------- | ------------------------------------------------ |
| `GET`    | `/api/health`                    | Check whether the backend is running             |
| `GET`    | `/api/summary`                   | View dashboard totals from local SQLite data     |
| `POST`   | `/api/check`                     | Check one website and save the result to history |
| `GET`    | `/api/history?limit=10&offset=0` | View paginated check history                     |
| `DELETE` | `/api/history`                   | Clear saved check history                        |
| `GET`    | `/api/sites`                     | List saved monitored sites                       |
| `POST`   | `/api/sites`                     | Save a monitored site                            |
| `PATCH`  | `/api/sites/{site_id}`           | Edit a saved site’s friendly name                |
| `DELETE` | `/api/sites/{site_id}`           | Delete a saved monitored site                    |
| `POST`   | `/api/sites/check-all`           | Check every saved monitored site                 |

Example website check request:

```json
{
  "url": "example.com"
}
```

Example website check response:

```json
{
  "input_url": "example.com",
  "normalized_url": "https://example.com",
  "final_url": "https://example.com",
  "hostname": "example.com",
  "is_up": true,
  "status_label": "healthy",
  "failure_type": null,
  "failure_stage": null,
  "status_code": 200,
  "response_time_ms": 123,
  "ip_addresses": ["93.184.216.34"],
  "checked_at": "2026-06-23T12:00:00+00:00",
  "error": null
}
```

## Local Data

Website check history and saved monitored sites are stored locally in SQLite. Database files are intentionally ignored by git so local runtime data is not committed.

Ignored database file types include:

```text
*.db
*.sqlite
*.sqlite3
```

## Roadmap

Planned improvements:

* History filtering and search
* Per-site detail summaries
* Response time trends
* Screenshots and deployment notes
* GitHub Actions test/build workflow

## Development Notes

This project is being built in small, focused milestones. Each milestone adds one clear piece of functionality and updates tests and documentation where practical.
