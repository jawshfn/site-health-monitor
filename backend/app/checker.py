from datetime import datetime, timezone
import socket
import time
from typing import Any
from urllib.parse import urlparse

import httpx


def normalize_url(url: str) -> str:
    cleaned_url = url.strip()

    if not cleaned_url:
        raise ValueError("URL cannot be empty.")

    parsed = urlparse(cleaned_url)
    if not parsed.scheme:
        cleaned_url = f"https://{cleaned_url}"
        parsed = urlparse(cleaned_url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must start with http:// or https://.")

    if not parsed.hostname:
        raise ValueError("URL must include a valid hostname.")

    return cleaned_url


def check_website(url: str) -> dict[str, Any]:
    checked_at = datetime.now(timezone.utc).isoformat()
    result: dict[str, Any] = {
        "input_url": url,
        "normalized_url": None,
        "final_url": None,
        "hostname": None,
        "status_code": None,
        "is_up": False,
        "response_time_ms": None,
        "ip_addresses": [],
        "checked_at": checked_at,
        "error": None,
    }

    try:
        normalized_url = normalize_url(url)
        parsed = urlparse(normalized_url)
        hostname = parsed.hostname

        if hostname is None:
            raise ValueError("URL must include a valid hostname.")

        result["normalized_url"] = normalized_url
        result["hostname"] = hostname
        result["ip_addresses"] = _resolve_hostname(hostname)

        start_time = time.perf_counter()
        response = httpx.get(normalized_url, follow_redirects=True, timeout=5.0)
        response_time_ms = round((time.perf_counter() - start_time) * 1000)

        result["status_code"] = response.status_code
        result["is_up"] = response.is_success
        result["response_time_ms"] = response_time_ms
        result["final_url"] = str(response.url)
    except Exception as exc:
        result["error"] = str(exc)

    return result


def _resolve_hostname(hostname: str) -> list[str]:
    addresses = socket.getaddrinfo(hostname, None)
    resolved_ips: set[str] = set()

    for address in addresses:
        ip_address = address[4][0]
        resolved_ips.add(str(ip_address))

    return sorted(resolved_ips)
