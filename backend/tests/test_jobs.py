from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from metadata_cleaner_core.api import create_app
from metadata_cleaner_core.engine.models import CleanResult, CleanStatus, FileJob


def _make_client(tmp_path, monkeypatch) -> TestClient:
    config_dir = tmp_path / "config"
    monkeypatch.setenv("METADATA_CLEANER_CONFIG_DIR", str(config_dir))
    return TestClient(create_app())


def _stub_result(path: Path) -> CleanResult:
    return CleanResult(
        job=FileJob(file_path=path),
        status=CleanStatus.SUCCESS,
        message="ok",
        cleaned_fields={"stub": True},
    )


def test_job_progress_and_log_download(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    dispatcher = client.app.state.dispatcher

    def fake_process_file_with_options(path, options):
        file_path = Path(path)
        return _stub_result(file_path)

    monkeypatch.setattr(dispatcher, "process_file_with_options", fake_process_file_with_options)

    payload_path = tmp_path / "file.txt"
    payload_path.write_text("data", encoding="utf-8")

    enqueue_resp = client.post("/api/jobs", json={"paths": [str(payload_path)]})
    assert enqueue_resp.status_code == 200
    job_id = enqueue_resp.json()["job_id"]

    with client.websocket_connect(f"/ws/jobs/{job_id}") as websocket:
        final_event: dict | None = None
        while True:
            message = websocket.receive_json()
            final_event = message
            if message.get("status") in {"success", "error"}:
                break

    assert final_event is not None
    assert final_event["status"] == "success"
    assert final_event["progress"]["overall_percent"] == 100.0
    file_progress = final_event["progress"]["files"][0]
    assert file_progress["status"] == "success"
    assert any(step["key"] == "cleaning" for step in file_progress["steps"])
    assert final_event["log"]["ready"] is True
    assert "json" in final_event["log"]["formats"]

    job_resp = client.get(f"/api/jobs/{job_id}")
    assert job_resp.status_code == 200
    job_payload = job_resp.json()
    assert job_payload["progress"]["overall_percent"] == 100.0
    assert job_payload["log"]["ready"] is True

    log_resp = client.get(f"/api/jobs/{job_id}/log")
    assert log_resp.status_code == 200
    assert log_resp.headers["content-type"].startswith("application/json")

    csv_resp = client.get(f"/api/jobs/{job_id}/log", params={"format": "csv"})
    assert csv_resp.status_code == 200
    assert csv_resp.headers["content-type"].startswith("text/csv")
