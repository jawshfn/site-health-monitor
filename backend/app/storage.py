import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(__file__).resolve().parents[1] / "site_health.db"


class DuplicateSavedSiteError(ValueError):
    pass


def initialize_database(db_path: Path | str | None = None) -> None:
    path = _get_database_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS website_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_url TEXT NOT NULL,
                normalized_url TEXT,
                final_url TEXT,
                hostname TEXT,
                is_up INTEGER NOT NULL,
                status_code INTEGER,
                response_time_ms INTEGER,
                ip_addresses TEXT NOT NULL,
                error TEXT,
                status_label TEXT,
                failure_type TEXT,
                failure_stage TEXT,
                checked_at TEXT NOT NULL
            )
            """
        )
        _ensure_column(connection, "website_checks", "status_label", "TEXT")
        _ensure_column(connection, "website_checks", "failure_type", "TEXT")
        _ensure_column(connection, "website_checks", "failure_stage", "TEXT")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                url TEXT NOT NULL,
                normalized_url TEXT NOT NULL,
                hostname TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def save_check_result(result: dict[str, Any], db_path: Path | str | None = None) -> int:
    initialize_database(db_path)
    path = _get_database_path(db_path)

    with sqlite3.connect(path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO website_checks (
                input_url,
                normalized_url,
                final_url,
                hostname,
                is_up,
                status_code,
                response_time_ms,
                ip_addresses,
                error,
                status_label,
                failure_type,
                failure_stage,
                checked_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.get("input_url"),
                result.get("normalized_url"),
                result.get("final_url"),
                result.get("hostname"),
                1 if result.get("is_up") else 0,
                result.get("status_code"),
                result.get("response_time_ms"),
                json.dumps(result.get("ip_addresses", [])),
                result.get("error"),
                result.get("status_label", "healthy" if result.get("is_up") else "unknown_error"),
                result.get("failure_type"),
                result.get("failure_stage"),
                result.get("checked_at"),
            ),
        )
        created_id = cursor.lastrowid

        if created_id is None:
            raise RuntimeError("Failed to save website check result.")

        return created_id


def get_recent_checks(
    limit: int = 20,
    offset: int = 0,
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    initialize_database(db_path)
    path = _get_database_path(db_path)

    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                id,
                input_url,
                normalized_url,
                final_url,
                hostname,
                is_up,
                status_code,
                response_time_ms,
                ip_addresses,
                error,
                status_label,
                failure_type,
                failure_stage,
                checked_at
            FROM website_checks
            ORDER BY id DESC
            LIMIT ?
            OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def count_check_history(db_path: Path | str | None = None) -> int:
    initialize_database(db_path)
    path = _get_database_path(db_path)

    with sqlite3.connect(path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM website_checks").fetchone()[0]

    return int(count)


def clear_check_history(db_path: Path | str | None = None) -> int:
    initialize_database(db_path)
    path = _get_database_path(db_path)

    with sqlite3.connect(path) as connection:
        cursor = connection.execute("DELETE FROM website_checks")

    return cursor.rowcount


def get_dashboard_summary(db_path: Path | str | None = None) -> dict[str, Any]:
    initialize_database(db_path)
    path = _get_database_path(db_path)

    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        saved_sites_count = connection.execute("SELECT COUNT(*) FROM saved_sites").fetchone()[0]
        total_checks = connection.execute("SELECT COUNT(*) FROM website_checks").fetchone()[0]
        average_response_time = connection.execute(
            """
            SELECT AVG(response_time_ms)
            FROM website_checks
            WHERE response_time_ms IS NOT NULL
            """
        ).fetchone()[0]
        rows = connection.execute(
            """
            SELECT id, normalized_url, hostname, is_up
            FROM website_checks
            ORDER BY id DESC
            """
        ).fetchall()

    latest_checks_by_site: dict[str, sqlite3.Row] = {}
    for row in rows:
        # Normalized URL is the best stable key for this schema. Hostname is a fallback
        # for older or invalid check rows that do not have a normalized URL.
        site_key = row["normalized_url"] or row["hostname"]
        if site_key and site_key not in latest_checks_by_site:
            latest_checks_by_site[site_key] = row

    latest_up_count = sum(1 for row in latest_checks_by_site.values() if row["is_up"])
    latest_down_count = len(latest_checks_by_site) - latest_up_count

    return {
        "saved_sites_count": int(saved_sites_count),
        "total_checks": int(total_checks),
        "latest_up_count": latest_up_count,
        "latest_down_count": latest_down_count,
        "average_response_time_ms": round(average_response_time, 2)
        if average_response_time is not None
        else None,
    }


def create_saved_site(
    url: str,
    normalized_url: str,
    hostname: str,
    name: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    initialize_database(db_path)
    path = _get_database_path(db_path)
    created_at = datetime.now(timezone.utc).isoformat()

    existing_site = get_saved_site_by_normalized_url(normalized_url, db_path)
    if existing_site is not None:
        raise DuplicateSavedSiteError("This site is already saved.")

    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            """
            INSERT INTO saved_sites (
                name,
                url,
                normalized_url,
                hostname,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, url, normalized_url, hostname, created_at),
        )
        created_id = cursor.lastrowid

        if created_id is None:
            raise RuntimeError("Failed to create saved site.")

        row = connection.execute(
            """
            SELECT id, name, url, normalized_url, hostname, created_at
            FROM saved_sites
            WHERE id = ?
            """,
            (created_id,),
        ).fetchone()

    return dict(row)


def get_saved_site_by_normalized_url(
    normalized_url: str,
    db_path: Path | str | None = None,
) -> dict[str, Any] | None:
    initialize_database(db_path)
    path = _get_database_path(db_path)

    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT id, name, url, normalized_url, hostname, created_at
            FROM saved_sites
            WHERE normalized_url = ?
            """,
            (normalized_url,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_saved_sites(db_path: Path | str | None = None) -> list[dict[str, Any]]:
    initialize_database(db_path)
    path = _get_database_path(db_path)

    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, name, url, normalized_url, hostname, created_at
            FROM saved_sites
            ORDER BY id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def update_saved_site_name(
    site_id: int,
    name: str | None,
    db_path: Path | str | None = None,
) -> dict[str, Any] | None:
    initialize_database(db_path)
    path = _get_database_path(db_path)

    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        existing_row = connection.execute(
            """
            SELECT id, name, url, normalized_url, hostname, created_at
            FROM saved_sites
            WHERE id = ?
            """,
            (site_id,),
        ).fetchone()

        if existing_row is None:
            return None

        connection.execute(
            """
            UPDATE saved_sites
            SET name = ?
            WHERE id = ?
            """,
            (name, site_id),
        )

        updated_row = connection.execute(
            """
            SELECT id, name, url, normalized_url, hostname, created_at
            FROM saved_sites
            WHERE id = ?
            """,
            (site_id,),
        ).fetchone()

        if updated_row is None:
            raise RuntimeError("Failed to update saved site.")

    return dict(updated_row)


def delete_saved_site(
    site_id: int,
    db_path: Path | str | None = None,
) -> dict[str, Any] | None:
    initialize_database(db_path)
    path = _get_database_path(db_path)

    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT id, name, url, normalized_url, hostname, created_at
            FROM saved_sites
            WHERE id = ?
            """,
            (site_id,),
        ).fetchone()

        if row is None:
            return None

        connection.execute(
            """
            DELETE FROM saved_sites
            WHERE id = ?
            """,
            (site_id,),
        )

    return dict(row)


def _get_database_path(db_path: Path | str | None) -> Path:
    if db_path is None:
        return Path(DATABASE_PATH)

    return Path(db_path)


def _ensure_column(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_type: str,
) -> None:
    columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing_column_names = {column[1] for column in columns}

    if column_name not in existing_column_names:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["is_up"] = bool(item["is_up"])
    item["ip_addresses"] = json.loads(item["ip_addresses"])
    if item.get("status_label") is None:
        item["status_label"] = "healthy" if item["is_up"] else "unknown_error"
    if item["is_up"]:
        item["failure_type"] = None
        item["failure_stage"] = None
    return item
