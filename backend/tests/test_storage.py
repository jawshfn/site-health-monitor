from app import storage


def test_save_check_result_and_get_recent_checks(tmp_path):
    db_path = tmp_path / "history.db"
    first_result = {
        "input_url": "example.com",
        "normalized_url": "https://example.com",
        "final_url": "https://example.com",
        "hostname": "example.com",
        "status_code": 200,
        "is_up": True,
        "response_time_ms": 123,
        "ip_addresses": ["93.184.216.34"],
        "checked_at": "2026-06-23T12:00:00+00:00",
        "error": None,
    }
    second_result = {
        "input_url": "bad-url",
        "normalized_url": None,
        "final_url": None,
        "hostname": None,
        "status_code": None,
        "is_up": False,
        "response_time_ms": None,
        "ip_addresses": [],
        "checked_at": "2026-06-23T12:01:00+00:00",
        "error": "URL must include a valid hostname.",
    }

    first_id = storage.save_check_result(first_result, db_path)
    second_id = storage.save_check_result(second_result, db_path)

    checks = storage.get_recent_checks(db_path=db_path)

    assert second_id > first_id
    assert [check["id"] for check in checks] == [second_id, first_id]
    assert checks[0]["is_up"] is False
    assert checks[0]["error"] == "URL must include a valid hostname."
    assert checks[1]["ip_addresses"] == ["93.184.216.34"]


def test_get_recent_checks_respects_limit(tmp_path):
    db_path = tmp_path / "history.db"

    for index in range(3):
        storage.save_check_result(
            {
                "input_url": f"example-{index}.com",
                "normalized_url": f"https://example-{index}.com",
                "final_url": f"https://example-{index}.com",
                "hostname": f"example-{index}.com",
                "status_code": 200,
                "is_up": True,
                "response_time_ms": 100 + index,
                "ip_addresses": [],
                "checked_at": f"2026-06-23T12:0{index}:00+00:00",
                "error": None,
            },
            db_path,
        )

    checks = storage.get_recent_checks(limit=2, db_path=db_path)

    assert len(checks) == 2
    assert checks[0]["input_url"] == "example-2.com"
    assert checks[1]["input_url"] == "example-1.com"


def test_create_and_list_saved_sites(tmp_path):
    db_path = tmp_path / "sites.db"

    first_site = storage.create_saved_site(
        url="example.com",
        normalized_url="https://example.com",
        hostname="example.com",
        name="Example",
        db_path=db_path,
    )
    second_site = storage.create_saved_site(
        url="https://github.com",
        normalized_url="https://github.com",
        hostname="github.com",
        db_path=db_path,
    )

    sites = storage.get_saved_sites(db_path)

    assert second_site["id"] > first_site["id"]
    assert [site["id"] for site in sites] == [second_site["id"], first_site["id"]]
    assert sites[0]["name"] is None
    assert sites[0]["hostname"] == "github.com"
    assert sites[1]["name"] == "Example"


def test_delete_saved_site(tmp_path):
    db_path = tmp_path / "sites.db"
    site = storage.create_saved_site(
        url="example.com",
        normalized_url="https://example.com",
        hostname="example.com",
        db_path=db_path,
    )

    deleted_site = storage.delete_saved_site(site["id"], db_path)
    sites = storage.get_saved_sites(db_path)

    assert deleted_site is not None
    assert deleted_site["id"] == site["id"]
    assert sites == []
    assert storage.delete_saved_site(site["id"], db_path) is None
