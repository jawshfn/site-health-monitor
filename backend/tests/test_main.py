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
