from fastapi.testclient import TestClient

from app import storage
from app.main import app


def test_check_endpoint_saves_result_and_history_returns_it(monkeypatch, tmp_path):
    db_path = tmp_path / "history.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    def fake_check_website(url):
        return {
            "input_url": url,
            "normalized_url": "https://example.com",
            "final_url": "https://example.com",
            "hostname": "example.com",
            "status_code": 200,
            "is_up": True,
            "response_time_ms": 42,
            "ip_addresses": ["93.184.216.34"],
            "checked_at": "2026-06-23T12:00:00+00:00",
            "error": None,
        }

    monkeypatch.setattr("app.main.check_website", fake_check_website)

    client = TestClient(app)
    check_response = client.post("/api/check", json={"url": "example.com"})
    history_response = client.get("/api/history")

    assert check_response.status_code == 200
    assert history_response.status_code == 200

    history = history_response.json()
    assert history["total"] == 1
    assert history["limit"] == 10
    assert history["offset"] == 0
    assert history["has_more"] is False
    assert len(history["items"]) == 1
    assert history["items"][0]["input_url"] == "example.com"
    assert history["items"][0]["normalized_url"] == "https://example.com"
    assert history["items"][0]["is_up"] is True


def test_clear_history_endpoint_removes_history_but_keeps_saved_sites(monkeypatch, tmp_path):
    db_path = tmp_path / "history.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    def fake_check_website(url):
        return {
            "input_url": url,
            "normalized_url": "https://example.com",
            "final_url": "https://example.com",
            "hostname": "example.com",
            "status_code": 200,
            "is_up": True,
            "response_time_ms": 42,
            "ip_addresses": ["93.184.216.34"],
            "checked_at": "2026-06-23T12:00:00+00:00",
            "error": None,
        }

    monkeypatch.setattr("app.main.check_website", fake_check_website)

    client = TestClient(app)
    client.post("/api/sites", json={"url": "example.com", "name": "Example"})
    client.post("/api/check", json={"url": "example.com"})
    client.post("/api/check", json={"url": "github.com"})

    clear_response = client.delete("/api/history")
    history_response = client.get("/api/history")
    sites_response = client.get("/api/sites")

    assert clear_response.status_code == 200
    assert clear_response.json() == {
        "deleted": True,
        "deleted_count": 2,
    }
    history = history_response.json()
    assert history["items"] == []
    assert history["total"] == 0
    sites = sites_response.json()
    assert len(sites) == 1
    assert sites[0]["hostname"] == "example.com"


def test_summary_endpoint_returns_empty_totals(monkeypatch, tmp_path):
    db_path = tmp_path / "summary.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    client = TestClient(app)
    response = client.get("/api/summary")

    assert response.status_code == 200
    assert response.json() == {
        "saved_sites_count": 0,
        "total_checks": 0,
        "latest_up_count": 0,
        "latest_down_count": 0,
        "average_response_time_ms": None,
    }


def test_summary_endpoint_counts_saved_sites_history_and_latest_status(monkeypatch, tmp_path):
    db_path = tmp_path / "summary.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    check_results = {
        "example.com": {
            "input_url": "example.com",
            "normalized_url": "https://example.com",
            "final_url": "https://example.com",
            "hostname": "example.com",
            "status_code": 200,
            "is_up": True,
            "response_time_ms": 100,
            "ip_addresses": [],
            "checked_at": "2026-06-23T12:00:00+00:00",
            "error": None,
        },
        "down.example": {
            "input_url": "down.example",
            "normalized_url": "https://down.example",
            "final_url": None,
            "hostname": "down.example",
            "status_code": None,
            "is_up": False,
            "response_time_ms": None,
            "ip_addresses": [],
            "checked_at": "2026-06-23T12:01:00+00:00",
            "error": "DNS lookup failed",
        },
        "https://example.com": {
            "input_url": "https://example.com",
            "normalized_url": "https://example.com",
            "final_url": "https://example.com",
            "hostname": "example.com",
            "status_code": 200,
            "is_up": True,
            "response_time_ms": 300,
            "ip_addresses": [],
            "checked_at": "2026-06-23T12:02:00+00:00",
            "error": None,
        },
    }

    def fake_check_website(url):
        return check_results[url]

    monkeypatch.setattr("app.main.check_website", fake_check_website)

    client = TestClient(app)
    client.post("/api/sites", json={"url": "example.com", "name": "Example"})
    client.post("/api/sites", json={"url": "down.example", "name": "Down"})
    client.post("/api/check", json={"url": "example.com"})
    client.post("/api/check", json={"url": "down.example"})
    client.post("/api/check", json={"url": "https://example.com"})

    response = client.get("/api/summary")

    assert response.status_code == 200
    assert response.json() == {
        "saved_sites_count": 2,
        "total_checks": 3,
        "latest_up_count": 1,
        "latest_down_count": 1,
        "average_response_time_ms": 200.0,
    }


def test_saved_sites_endpoints_create_list_and_delete(monkeypatch, tmp_path):
    db_path = tmp_path / "sites.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    client = TestClient(app)
    create_response = client.post(
        "/api/sites",
        json={
            "url": "example.com",
            "name": "Example",
        },
    )
    list_response = client.get("/api/sites")

    assert create_response.status_code == 200
    created_site = create_response.json()
    assert created_site["name"] == "Example"
    assert created_site["url"] == "example.com"
    assert created_site["normalized_url"] == "https://example.com"
    assert created_site["hostname"] == "example.com"

    assert list_response.status_code == 200
    sites = list_response.json()
    assert len(sites) == 1
    assert sites[0]["id"] == created_site["id"]

    delete_response = client.delete(f"/api/sites/{created_site['id']}")
    empty_list_response = client.get("/api/sites")

    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True
    assert empty_list_response.json() == []


def test_saved_sites_endpoint_rejects_duplicate_normalized_url(monkeypatch, tmp_path):
    db_path = tmp_path / "sites.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    client = TestClient(app)
    first_response = client.post(
        "/api/sites",
        json={
            "url": "example.com",
            "name": "Example",
        },
    )
    duplicate_response = client.post(
        "/api/sites",
        json={
            "url": "https://example.com",
            "name": "Duplicate Example",
        },
    )
    list_response = client.get("/api/sites")

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "This site is already saved.",
    }

    sites = list_response.json()
    assert len(sites) == 1
    assert sites[0]["url"] == "example.com"
    assert sites[0]["normalized_url"] == "https://example.com"


def test_saved_sites_endpoint_updates_name(monkeypatch, tmp_path):
    db_path = tmp_path / "sites.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    client = TestClient(app)
    created_site = client.post(
        "/api/sites",
        json={
            "url": "example.com",
            "name": "Example",
        },
    ).json()

    update_response = client.patch(
        f"/api/sites/{created_site['id']}",
        json={"name": "  Docs Site  "},
    )

    assert update_response.status_code == 200
    updated_site = update_response.json()
    assert updated_site["id"] == created_site["id"]
    assert updated_site["name"] == "Docs Site"
    assert updated_site["url"] == created_site["url"]
    assert updated_site["normalized_url"] == created_site["normalized_url"]
    assert updated_site["hostname"] == created_site["hostname"]
    assert updated_site["created_at"] == created_site["created_at"]


def test_saved_sites_endpoint_clears_name(monkeypatch, tmp_path):
    db_path = tmp_path / "sites.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    client = TestClient(app)
    created_site = client.post(
        "/api/sites",
        json={
            "url": "example.com",
            "name": "Example",
        },
    ).json()

    update_response = client.patch(
        f"/api/sites/{created_site['id']}",
        json={"name": "   "},
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] is None


def test_saved_sites_endpoint_update_missing_site_returns_404(monkeypatch, tmp_path):
    db_path = tmp_path / "sites.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    client = TestClient(app)
    response = client.patch("/api/sites/999", json={"name": "Missing"})

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Saved site not found.",
    }


def test_check_all_saved_sites_returns_empty_summary(monkeypatch, tmp_path):
    db_path = tmp_path / "sites.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    client = TestClient(app)
    response = client.post("/api/sites/check-all")

    assert response.status_code == 200
    assert response.json() == {
        "total": 0,
        "up": 0,
        "down": 0,
        "results": [],
    }


def test_check_all_saved_sites_checks_each_site_and_saves_history(monkeypatch, tmp_path):
    db_path = tmp_path / "sites.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    def fake_check_website(url):
        is_example = url == "https://example.com"
        return {
            "input_url": url,
            "normalized_url": url,
            "final_url": url if is_example else None,
            "hostname": "example.com" if is_example else "down.example",
            "status_code": 200 if is_example else None,
            "is_up": is_example,
            "response_time_ms": 42 if is_example else None,
            "ip_addresses": ["93.184.216.34"] if is_example else [],
            "checked_at": "2026-06-23T12:00:00+00:00",
            "error": None if is_example else "DNS lookup failed",
        }

    monkeypatch.setattr("app.main.check_website", fake_check_website)

    client = TestClient(app)
    first_site = client.post(
        "/api/sites",
        json={
            "url": "example.com",
            "name": "Example",
        },
    ).json()
    second_site = client.post(
        "/api/sites",
        json={
            "url": "down.example",
            "name": "Down Site",
        },
    ).json()

    response = client.post("/api/sites/check-all")
    history_response = client.get("/api/history?limit=5")

    assert response.status_code == 200
    summary = response.json()
    assert summary["total"] == 2
    assert summary["up"] == 1
    assert summary["down"] == 1
    assert [result["site_id"] for result in summary["results"]] == [
        second_site["id"],
        first_site["id"],
    ]
    assert summary["results"][0]["name"] == "Down Site"
    assert summary["results"][0]["is_up"] is False
    assert summary["results"][0]["error"] == "DNS lookup failed"
    assert summary["results"][1]["name"] == "Example"
    assert summary["results"][1]["is_up"] is True

    history = history_response.json()
    assert len(history["items"]) == 2
    assert history["total"] == 2
    assert history["items"][0]["normalized_url"] == "https://example.com"
    assert history["items"][1]["normalized_url"] == "https://down.example"


def test_history_endpoint_supports_limit_offset_total_and_has_more(monkeypatch, tmp_path):
    db_path = tmp_path / "history.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    def fake_check_website(url):
        return {
            "input_url": url,
            "normalized_url": f"https://{url}",
            "final_url": f"https://{url}",
            "hostname": url,
            "status_code": 200,
            "is_up": True,
            "response_time_ms": 42,
            "ip_addresses": [],
            "checked_at": "2026-06-23T12:00:00+00:00",
            "error": None,
        }

    monkeypatch.setattr("app.main.check_website", fake_check_website)

    client = TestClient(app)
    for index in range(5):
        client.post("/api/check", json={"url": f"example-{index}.com"})

    first_page = client.get("/api/history?limit=2&offset=0").json()
    second_page = client.get("/api/history?limit=2&offset=2").json()
    final_page = client.get("/api/history?limit=2&offset=4").json()

    assert first_page["total"] == 5
    assert first_page["limit"] == 2
    assert first_page["offset"] == 0
    assert first_page["has_more"] is True
    assert [item["input_url"] for item in first_page["items"]] == [
        "example-4.com",
        "example-3.com",
    ]

    assert second_page["total"] == 5
    assert second_page["offset"] == 2
    assert second_page["has_more"] is True
    assert [item["input_url"] for item in second_page["items"]] == [
        "example-2.com",
        "example-1.com",
    ]

    assert final_page["total"] == 5
    assert final_page["offset"] == 4
    assert final_page["has_more"] is False
    assert [item["input_url"] for item in final_page["items"]] == ["example-0.com"]


def test_history_endpoint_filters_by_exact_status_label(monkeypatch, tmp_path):
    _seed_history_filter_checks(monkeypatch, tmp_path)

    client = TestClient(app)
    response = client.get("/api/history?status_label=timeout")

    assert response.status_code == 200
    history = response.json()
    assert history["total"] == 1
    assert history["status_label"] == "timeout"
    assert history["items"][0]["hostname"] == "slow.example"
    assert history["items"][0]["status_label"] == "timeout"


def test_history_endpoint_issue_filter_returns_non_healthy_checks(monkeypatch, tmp_path):
    _seed_history_filter_checks(monkeypatch, tmp_path)

    client = TestClient(app)
    response = client.get("/api/history?status_label=issue")

    assert response.status_code == 200
    history = response.json()
    assert history["total"] == 3
    assert {item["status_label"] for item in history["items"]} == {
        "http_error",
        "timeout",
        "dns_error",
    }


def test_history_endpoint_searches_hostname_and_url(monkeypatch, tmp_path):
    _seed_history_filter_checks(monkeypatch, tmp_path)

    client = TestClient(app)
    hostname_response = client.get("/api/history?search=api")
    url_response = client.get("/api/history?search=docs.example")

    assert hostname_response.status_code == 200
    assert hostname_response.json()["total"] == 1
    assert hostname_response.json()["items"][0]["hostname"] == "api.example.com"

    assert url_response.status_code == 200
    assert url_response.json()["total"] == 1
    assert url_response.json()["items"][0]["normalized_url"] == "https://docs.example.com"


def test_history_endpoint_empty_search_returns_unfiltered_results(monkeypatch, tmp_path):
    _seed_history_filter_checks(monkeypatch, tmp_path)

    client = TestClient(app)
    response = client.get("/api/history?search=   ")

    assert response.status_code == 200
    history = response.json()
    assert history["total"] == 5
    assert history["search"] is None


def test_history_endpoint_one_character_search_is_ignored(monkeypatch, tmp_path):
    _seed_history_filter_checks(monkeypatch, tmp_path)

    client = TestClient(app)
    response = client.get("/api/history?search=m")

    assert response.status_code == 200
    history = response.json()
    assert history["total"] == 5
    assert history["search"] is None


def test_history_endpoint_two_character_search_filters_results(monkeypatch, tmp_path):
    _seed_history_filter_checks(monkeypatch, tmp_path)

    client = TestClient(app)
    response = client.get("/api/history?search=sl")

    assert response.status_code == 200
    history = response.json()
    assert history["total"] == 1
    assert history["search"] == "sl"
    assert history["items"][0]["hostname"] == "slow.example"


def test_history_endpoint_combines_filter_search_total_and_items(monkeypatch, tmp_path):
    _seed_history_filter_checks(monkeypatch, tmp_path)

    client = TestClient(app)
    response = client.get("/api/history?status_label=issue&search=example.com")

    assert response.status_code == 200
    history = response.json()
    assert history["total"] == 1
    assert history["search"] == "example.com"
    assert history["items"][0]["hostname"] == "api.example.com"
    assert history["items"][0]["status_label"] == "http_error"


def test_history_endpoint_paginates_filtered_results(monkeypatch, tmp_path):
    _seed_history_filter_checks(monkeypatch, tmp_path)

    client = TestClient(app)
    first_page = client.get("/api/history?status_label=healthy&limit=1&offset=0").json()
    second_page = client.get("/api/history?status_label=healthy&limit=1&offset=1").json()

    assert first_page["total"] == 2
    assert first_page["has_more"] is True
    assert len(first_page["items"]) == 1
    assert first_page["items"][0]["hostname"] == "docs.example.com"

    assert second_page["total"] == 2
    assert second_page["has_more"] is False
    assert len(second_page["items"]) == 1
    assert second_page["items"][0]["hostname"] == "example.com"


def _seed_history_filter_checks(monkeypatch, tmp_path):
    db_path = tmp_path / "history-filter.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", db_path)

    check_results = {
        "example.com": _history_filter_result(
            input_url="example.com",
            normalized_url="https://example.com",
            final_url="https://example.com",
            hostname="example.com",
            is_up=True,
            status_label="healthy",
            status_code=200,
        ),
        "api.example.com/missing": _history_filter_result(
            input_url="api.example.com/missing",
            normalized_url="https://api.example.com/missing",
            final_url="https://api.example.com/missing",
            hostname="api.example.com",
            is_up=False,
            status_label="http_error",
            status_code=404,
        ),
        "slow.example": _history_filter_result(
            input_url="slow.example",
            normalized_url="https://slow.example",
            final_url=None,
            hostname="slow.example",
            is_up=False,
            status_label="timeout",
            status_code=None,
        ),
        "missing.test": _history_filter_result(
            input_url="missing.test",
            normalized_url="https://missing.test",
            final_url=None,
            hostname="missing.test",
            is_up=False,
            status_label="dns_error",
            status_code=None,
        ),
        "docs.example": _history_filter_result(
            input_url="docs.example",
            normalized_url="https://docs.example.com",
            final_url="https://docs.example.com",
            hostname="docs.example.com",
            is_up=True,
            status_label="healthy",
            status_code=200,
        ),
    }

    def fake_check_website(url):
        return check_results[url]

    monkeypatch.setattr("app.main.check_website", fake_check_website)

    client = TestClient(app)
    for url in check_results:
        client.post("/api/check", json={"url": url})


def _history_filter_result(
    input_url,
    normalized_url,
    final_url,
    hostname,
    is_up,
    status_label,
    status_code,
):
    return {
        "input_url": input_url,
        "normalized_url": normalized_url,
        "final_url": final_url,
        "hostname": hostname,
        "status_code": status_code,
        "is_up": is_up,
        "status_label": status_label,
        "failure_type": None if is_up else status_label,
        "failure_stage": None if is_up else "http",
        "dns_status": "resolved" if status_label != "dns_error" else "failed",
        "connection_status": "connected" if status_label not in ("dns_error",) else "not_checked",
        "http_status": "response_received" if status_code else "not_attempted",
        "diagnostic_summary": f"Observed {status_label}.",
        "response_time_ms": 42 if status_code else None,
        "ip_addresses": [],
        "checked_at": "2026-06-23T12:00:00+00:00",
        "error": None if is_up else f"Observed {status_label}.",
    }
