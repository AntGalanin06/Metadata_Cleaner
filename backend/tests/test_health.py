import pytest
import time

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from metadata_cleaner_core.api import create_app


def _make_client(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    monkeypatch.setenv("METADATA_CLEANER_CONFIG_DIR", str(config_dir))
    return TestClient(create_app())


def test_healthcheck(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_supported_extensions_endpoint(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    response = client.get("/legacy/extensions")
    assert response.status_code == 200
    data = response.json()
    assert "extensions" in data
    assert ".jpg" in data["extensions"]


def test_metadata_catalogue_endpoint(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    response = client.get("/api/metadata/fields")
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert "categories" in payload
    assert "author" in payload["categories"]
    image_entry = next(item for item in payload["items"] if item["file_type"] == "image")
    assert any(field["key"] == "exif_author" for field in image_entry["fields"])


def test_settings_roundtrip(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)

    read_response = client.get("/api/settings")
    assert read_response.status_code == 200
    original = read_response.json()["settings"]

    payload = {"data": {"language": "ru"}}
    write_response = client.put("/api/settings", json=payload)
    assert write_response.status_code == 200
    assert write_response.json()["settings"]["language"] == "ru"

    # Ensure persisted change is returned on next read
    read_again = client.get("/api/settings")
    assert read_again.status_code == 200
    assert read_again.json()["settings"]["language"] == "ru"


def test_process_endpoint_handles_unknown_file(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    fake_file = tmp_path / "unknown.xyz"
    fake_file.write_text("placeholder")

    response = client.post("/api/process", json={"paths": [str(fake_file)]})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["job_id"] is None
    assert body["results"][0]["status"] == "error"


def test_settings_schema_endpoint(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    response = client.get("/api/settings/schema")
    assert response.status_code == 200
    payload = response.json()
    assert "defaults" in payload
    assert "file_type_defaults" in payload
    assert "image" in payload["file_type_defaults"]
    assert "theme_options" in payload and "system" in payload["theme_options"]
    assert "output_modes" in payload and "create_copy" in payload["output_modes"]


def test_job_queue_processes_in_background(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    fake_file = tmp_path / "unknown.xyz"
    fake_file.write_text("placeholder")

    enqueue_resp = client.post("/api/jobs", json={"paths": [str(fake_file)]})
    assert enqueue_resp.status_code == 200
    job_id = enqueue_resp.json()["job_id"]

    # Poll the job endpoint until completion or timeout
    for _ in range(10):
        job_resp = client.get(f"/api/jobs/{job_id}")
        assert job_resp.status_code == 200
        payload = job_resp.json()
        if payload["status"] in {"success", "error"}:
            break
        time.sleep(0.05)
    else:
        raise AssertionError("job did not finish in time")

    assert payload["status"] == "error"
    assert payload["results"], "job results should be present"


def test_job_websocket_stream(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    fake_file = tmp_path / "unknown.xyz"
    fake_file.write_text("placeholder")

    enqueue_resp = client.post("/api/jobs", json={"paths": [str(fake_file)]})
    assert enqueue_resp.status_code == 200
    job_id = enqueue_resp.json()["job_id"]

    statuses = []
    with client.websocket_connect(f"/ws/jobs/{job_id}") as websocket:
        try:
            while True:
                event = websocket.receive_json()
                statuses.append(event["status"])
                if event["status"] in {"success", "error"}:
                    break
        except WebSocketDisconnect:
            pass
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_json()

    assert statuses, "должны получить хотя бы одно сообщение"
    assert statuses[-1] == "error"
