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
