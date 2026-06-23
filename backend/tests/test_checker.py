import socket

import httpx
import pytest

from app import checker
from app.checker import check_website, normalize_url


def test_normalize_url_adds_https_when_scheme_is_missing():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_url_keeps_http_scheme():
    assert normalize_url("http://example.com") == "http://example.com"


def test_normalize_url_raises_for_empty_url():
    with pytest.raises(ValueError):
        normalize_url("")


def test_check_website_marks_2xx_response_healthy(monkeypatch):
    monkeypatch.setattr(checker, "_resolve_hostname", lambda hostname: ["93.184.216.34"])
    monkeypatch.setattr(
        checker.httpx,
        "get",
        lambda url, follow_redirects, timeout: httpx.Response(
            200,
            request=httpx.Request("GET", url),
        ),
    )

    result = check_website("example.com")

    assert result["status_label"] == "healthy"
    assert result["failure_type"] is None
    assert result["failure_stage"] is None
    assert result["is_up"] is True


def test_check_website_marks_3xx_response_healthy(monkeypatch):
    monkeypatch.setattr(checker, "_resolve_hostname", lambda hostname: ["93.184.216.34"])
    monkeypatch.setattr(
        checker.httpx,
        "get",
        lambda url, follow_redirects, timeout: httpx.Response(
            302,
            headers={"location": "https://example.com/new"},
            request=httpx.Request("GET", url),
        ),
    )

    result = check_website("example.com")

    assert result["status_label"] == "healthy"
    assert result["is_up"] is True


def test_check_website_marks_404_response_http_error(monkeypatch):
    monkeypatch.setattr(checker, "_resolve_hostname", lambda hostname: ["93.184.216.34"])
    monkeypatch.setattr(
        checker.httpx,
        "get",
        lambda url, follow_redirects, timeout: httpx.Response(
            404,
            request=httpx.Request("GET", url),
        ),
    )

    result = check_website("example.com/missing")

    assert result["status_label"] == "http_error"
    assert result["failure_type"] == "http_error"
    assert result["failure_stage"] == "http"
    assert result["is_up"] is False
    assert result["status_code"] == 404
    assert result["error"] is None


def test_check_website_marks_500_response_http_error(monkeypatch):
    monkeypatch.setattr(checker, "_resolve_hostname", lambda hostname: ["93.184.216.34"])
    monkeypatch.setattr(
        checker.httpx,
        "get",
        lambda url, follow_redirects, timeout: httpx.Response(
            500,
            request=httpx.Request("GET", url),
        ),
    )

    result = check_website("example.com")

    assert result["status_label"] == "http_error"
    assert result["is_up"] is False
    assert result["status_code"] == 500


def test_check_website_marks_timeout(monkeypatch):
    def raise_timeout(url, follow_redirects, timeout):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(checker, "_resolve_hostname", lambda hostname: ["93.184.216.34"])
    monkeypatch.setattr(checker.httpx, "get", raise_timeout)

    result = check_website("example.com")

    assert result["status_label"] == "timeout"
    assert result["failure_type"] == "timeout"
    assert result["failure_stage"] == "http"
    assert result["is_up"] is False
    assert result["response_time_ms"] is not None


def test_check_website_marks_dns_error(monkeypatch):
    def raise_dns_error(hostname):
        raise socket.gaierror("lookup failed")

    monkeypatch.setattr(checker, "_resolve_hostname", raise_dns_error)

    result = check_website("missing.example")

    assert result["status_label"] == "dns_error"
    assert result["failure_type"] == "dns_error"
    assert result["failure_stage"] == "dns"
    assert result["is_up"] is False


def test_check_website_marks_connection_error(monkeypatch):
    def raise_connection_error(url, follow_redirects, timeout):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(checker, "_resolve_hostname", lambda hostname: ["93.184.216.34"])
    monkeypatch.setattr(checker.httpx, "get", raise_connection_error)

    result = check_website("example.com")

    assert result["status_label"] == "connection_error"
    assert result["failure_type"] == "connection_error"
    assert result["failure_stage"] == "connection"
    assert result["is_up"] is False


def test_check_website_marks_invalid_url():
    result = check_website("")

    assert result["status_label"] == "invalid_url"
    assert result["failure_type"] == "invalid_url"
    assert result["failure_stage"] == "validation"
    assert result["is_up"] is False
