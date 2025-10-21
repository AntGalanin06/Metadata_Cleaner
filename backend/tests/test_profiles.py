from fastapi.testclient import TestClient

from metadata_cleaner_core.api import create_app


def _make_client(tmp_path, monkeypatch) -> TestClient:
    config_dir = tmp_path / "config"
    monkeypatch.setenv("METADATA_CLEANER_CONFIG_DIR", str(config_dir))
    return TestClient(create_app())


def test_profile_crud_flow(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)

    list_resp = client.get("/api/settings/profiles")
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert payload["active_id"] == "default"
    default_profile = payload["profiles"][0]

    new_payload = {
        "name": "Raw Photography",
        "description": "Disable GPS data removal for images",
        "file_type_settings": {
            **default_profile["file_type_settings"],
            "image": {
                **default_profile["file_type_settings"]["image"],
                "exif_gps": False,
            },
        },
    }

    create_resp = client.post("/api/settings/profiles", json=new_payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["name"] == "Raw Photography"
    profile_id = created["id"]

    update_resp = client.put(
        f"/api/settings/profiles/{profile_id}",
        json={"name": "RAW Editing"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "RAW Editing"

    activate_resp = client.post(f"/api/settings/profiles/{profile_id}/activate")
    assert activate_resp.status_code == 200
    assert activate_resp.json()["active_id"] == profile_id

    delete_resp = client.delete(f"/api/settings/profiles/{profile_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json() == {"status": "deleted", "profile_id": profile_id}

    list_after = client.get("/api/settings/profiles")
    assert list_after.status_code == 200
    assert list_after.json()["active_id"] == "default"


def test_profile_delete_default_forbidden(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    response = client.delete("/api/settings/profiles/default")
    assert response.status_code == 400
    assert response.json()["detail"] == "cannot delete default profile"


def test_profile_not_found(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    response = client.put(
        "/api/settings/profiles/unknown", json={"name": "Missing"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found"


def test_profile_websocket_stream(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)

    with client.websocket_connect("/ws/settings/profiles") as websocket:
        snapshot = websocket.receive_json()
        assert snapshot["event"] == "profiles_snapshot"
        assert snapshot["active_id"] == "default"

        create_resp = client.post(
            "/api/settings/profiles",
            json={"name": "Shot"},
        )
        assert create_resp.status_code == 201

        created_event = websocket.receive_json()
        assert created_event["event"] == "profile_created"
        assert created_event["profile"]["name"] == "Shot"

        profile_id = create_resp.json()["id"]
        activate_resp = client.post(f"/api/settings/profiles/{profile_id}/activate")
        assert activate_resp.status_code == 200

        activated_event = websocket.receive_json()
        assert activated_event["event"] == "profile_activated"
        assert activated_event["active_id"] == profile_id


def test_profile_unknown_settings_are_sanitized(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    response = client.post(
        "/api/settings/profiles",
        json={
            "name": "Batch",
            "file_type_settings": {"unknown": {"foo": True}},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "unknown" not in data["file_type_settings"]
