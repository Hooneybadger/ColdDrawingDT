from __future__ import annotations

import json
from datetime import timedelta

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from cold_drawing_twin.api.app import create_app
from cold_drawing_twin.observability.gpu import read_nvidia_smi
from cold_drawing_twin.observability.metrics import scrape_runtime_gauges
from cold_drawing_twin.orchestration.container import build_container
from cold_drawing_twin.stream.sessions import STREAM_STORE, StreamSessionStore
from tests.conftest import PRIMARY, make_pinn


def test_read_nvidia_smi_parses_csv(monkeypatch):
    class Result:
        returncode = 0
        stdout = "0, 41, 1024, 8192\n"

    samples = read_nvidia_smi(runner=lambda *_args, **_kwargs: Result())
    assert len(samples) == 1
    assert samples[0].index == "0"
    assert samples[0].utilization_ratio == 0.41
    assert samples[0].memory_used_bytes == 1024 * 1024 * 1024
    assert samples[0].memory_total_bytes == 8192 * 1024 * 1024


def test_read_nvidia_smi_missing_binary():
    def boom(*_args, **_kwargs):
        raise FileNotFoundError("nvidia-smi")

    assert read_nvidia_smi(runner=boom) == []


def test_expired_session_is_dropped():
    store = StreamSessionStore(ttl_s=1)
    session = store.create(role="operator", client="kit", asset_id=PRIMARY)
    later = session.last_heartbeat + timedelta(seconds=2)
    assert store.get(session.session_id, now=later) is None
    assert store.active(now=later) == []


def test_stream_session_api_and_metrics(settings, monkeypatch):
    STREAM_STORE.clear()
    monkeypatch.setattr("cold_drawing_twin.observability.gpu.read_nvidia_smi", lambda: [])
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    client = TestClient(create_app(container))
    created = client.post(
        "/stream/sessions",
        json={"role": "operator", "client": "browser", "asset_id": PRIMARY},
    )
    assert created.status_code == 200
    session_id = created.json()["session_id"]
    pulse = client.post(
        f"/stream/sessions/{session_id}/heartbeat",
        json={
            "gpu": {
                "index": "0",
                "utilization_ratio": 0.2,
                "memory_used_bytes": 1000,
                "memory_total_bytes": 8000,
            }
        },
    )
    assert pulse.status_code == 200
    listed = client.get("/stream/sessions").json()
    assert len(listed["sessions"]) == 1
    scrape_runtime_gauges(container.open())
    assert REGISTRY.get_sample_value("stream_sessions", {"role": "operator", "client": "browser"}) == 1.0
    assert REGISTRY.get_sample_value("gpu_devices") == 1.0
    assert REGISTRY.get_sample_value("gpu_utilization_ratio", {"gpu": "0"}) == 0.2
    ended = client.delete(f"/stream/sessions/{session_id}")
    assert ended.status_code == 200
    scrape_runtime_gauges(container.open())
    assert REGISTRY.get_sample_value("stream_sessions", {"role": "operator", "client": "browser"}) == 0.0
