import json
import sqlite3
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(__file__).resolve().parents[1] / "site_health.db"


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
                checked_at TEXT NOT NULL
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
                checked_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                result.get("checked_at"),
            ),
        )
        return int(cursor.lastrowid)


def get_recent_checks(
    limit: int = 20,
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
                checked_at
            FROM website_checks
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def _get_database_path(db_path: Path | str | None) -> Path:
    if db_path is None:
        return Path(DATABASE_PATH)

    return Path(db_path)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["is_up"] = bool(item["is_up"])
    item["ip_addresses"] = json.loads(item["ip_addresses"])
    return item
