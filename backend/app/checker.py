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
    start_time: float | None = None
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
        "status_label": "unknown_error",
        "failure_type": "unknown_error",
        "failure_stage": "unknown",
        "dns_status": "not_checked",
        "connection_status": "not_checked",
        "http_status": "not_attempted",
        "diagnostic_summary": "The check did not complete.",
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
        result["dns_status"] = "resolved"

        port = 443 if parsed.scheme == "https" else 80
        _check_tcp_connection(hostname, port)
        result["connection_status"] = "connected"

        start_time = time.perf_counter()
        response = httpx.get(normalized_url, follow_redirects=True, timeout=5.0)
        response_time_ms = round((time.perf_counter() - start_time) * 1000)
        is_healthy = 200 <= response.status_code < 400

        result["status_code"] = response.status_code
        result["is_up"] = is_healthy
        result["response_time_ms"] = response_time_ms
        result["final_url"] = str(response.url)
        result["status_label"] = "healthy" if is_healthy else "http_error"
        result["failure_type"] = None if is_healthy else "http_error"
        result["failure_stage"] = None if is_healthy else "http"
        result["http_status"] = "response_received"
        result["diagnostic_summary"] = (
            "DNS resolved, connection established, and the HTTP response was healthy."
            if is_healthy
            else f"The server responded with HTTP {response.status_code}."
        )
    except ValueError as exc:
        result["error"] = str(exc)
        result["status_label"] = "invalid_url"
        result["failure_type"] = "invalid_url"
        result["failure_stage"] = "validation"
        result["diagnostic_summary"] = "The URL could not be checked because it is invalid."
    except socket.gaierror as exc:
        result["error"] = f"DNS lookup failed: {exc}"
        result["status_label"] = "dns_error"
        result["failure_type"] = "dns_error"
        result["failure_stage"] = "dns"
        result["dns_status"] = "failed"
        result["connection_status"] = "not_checked"
        result["http_status"] = "not_attempted"
        result["diagnostic_summary"] = "DNS lookup failed, so no connection attempt was made."
    except (socket.timeout, TimeoutError, OSError) as exc:
        result["error"] = f"Connection failed: {exc}"
        result["status_label"] = "connection_error"
        result["failure_type"] = "connection_error"
        result["failure_stage"] = "connection"
        result["connection_status"] = "failed"
        result["http_status"] = "not_attempted"
        result["diagnostic_summary"] = (
            "DNS resolved, but the TCP connection could not be established."
        )
    except httpx.TimeoutException as exc:
        result["error"] = "No HTTP response was received before the timeout."
        if start_time is not None:
            result["response_time_ms"] = round((time.perf_counter() - start_time) * 1000)
        result["status_label"] = "timeout"
        result["failure_type"] = "timeout"
        result["failure_stage"] = "http"
        result["http_status"] = "timeout"
        result["diagnostic_summary"] = (
            "DNS resolved and connection established, but the HTTP request timed out."
        )
    except httpx.ConnectError as exc:
        result["error"] = f"Connection failed: {exc}"
        if start_time is not None:
            result["response_time_ms"] = round((time.perf_counter() - start_time) * 1000)
        result["status_label"] = "connection_error"
        result["failure_type"] = "connection_error"
        result["failure_stage"] = "connection"
        result["http_status"] = "failed"
        result["diagnostic_summary"] = (
            "DNS resolved and connection established, but the HTTP request failed."
        )
    except httpx.NetworkError as exc:
        result["error"] = f"Connection failed: {exc}"
        if start_time is not None:
            result["response_time_ms"] = round((time.perf_counter() - start_time) * 1000)
        result["status_label"] = "connection_error"
        result["failure_type"] = "connection_error"
        result["failure_stage"] = "connection"
        result["http_status"] = "failed"
        result["diagnostic_summary"] = (
            "DNS resolved and connection established, but the HTTP request failed."
        )
    except Exception as exc:
        result["error"] = str(exc)
        result["status_label"] = "unknown_error"
        result["failure_type"] = "unknown_error"
        result["failure_stage"] = "unknown"
        result["diagnostic_summary"] = "This checker encountered an unexpected error."

    return result


def _resolve_hostname(hostname: str) -> list[str]:
    addresses = socket.getaddrinfo(hostname, None)
    resolved_ips: set[str] = set()

    for address in addresses:
        ip_address = address[4][0]
        resolved_ips.add(str(ip_address))

    return sorted(resolved_ips)


def _check_tcp_connection(hostname: str, port: int, timeout: float = 3.0) -> None:
    with socket.create_connection((hostname, port), timeout=timeout):
        return
