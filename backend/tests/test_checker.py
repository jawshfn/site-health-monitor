import pytest

from app.checker import normalize_url


def test_normalize_url_adds_https_when_scheme_is_missing():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_url_keeps_http_scheme():
    assert normalize_url("http://example.com") == "http://example.com"


def test_normalize_url_raises_for_empty_url():
    with pytest.raises(ValueError):
        normalize_url("")
