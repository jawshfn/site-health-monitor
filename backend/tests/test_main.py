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
    assert len(history) == 1
    assert history[0]["input_url"] == "example.com"
    assert history[0]["normalized_url"] == "https://example.com"
    assert history[0]["is_up"] is True


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
