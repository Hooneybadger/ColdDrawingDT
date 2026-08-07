from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from cold_drawing_twin.api.app import create_app
from cold_drawing_twin.orchestration.container import build_container
from cold_drawing_twin.simulation.solver.openradioss import SolverError
from tests.conftest import DEMO, PRIMARY, make_pinn


def test_fast_path_increments_decision_and_pinn_counters(settings):
    before_decisions = REGISTRY.get_sample_value("decisions_total", {"verdict": "SAFE"}) or 0.0
    before_pinn = REGISTRY.get_sample_value("pinn_results_total", {"verdict": "SAFE", "model_version": "v0.1.1"}) or 0.0
    before_twin = REGISTRY.get_sample_value("twin_updates_total", {"asset_id": PRIMARY, "status": "GOOD"}) or 0.0
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    evaluation.start_operational(PRIMARY)
    after_decisions = REGISTRY.get_sample_value("decisions_total", {"verdict": "SAFE"}) or 0.0
    after_pinn = REGISTRY.get_sample_value("pinn_results_total", {"verdict": "SAFE", "model_version": "v0.1.1"}) or 0.0
    after_twin = REGISTRY.get_sample_value("twin_updates_total", {"asset_id": PRIMARY, "status": "GOOD"}) or 0.0
    assert after_decisions >= before_decisions + 1
    assert after_pinn >= before_pinn + 1
    assert after_twin >= before_twin + 1


def test_scrape_sets_twin_age_and_queue_depth(tmp_path):
    from datetime import timedelta

    from cold_drawing_twin.observability.metrics import scrape_runtime_gauges
    from cold_drawing_twin.settings import Settings

    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'gauges.db'}",
        fea_execution="celery",
        basyx_enabled=False,
        openradioss_work_dir=tmp_path / "fea",
        openradioss_starter_bin="",
        openradioss_engine_bin="",
        pinn_model_dir=tmp_path / "missing-pinn",
        _env_file=None,
    )
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(
        PRIMARY,
        DEMO,
        source_timestamp=datetime.now(timezone.utc) - timedelta(seconds=5),
        quality="GOOD",
    )
    evaluation.start_operational(PRIMARY)
    scrape_runtime_gauges(session)
    age = REGISTRY.get_sample_value("twin_state_age_seconds", {"asset_id": PRIMARY})
    depth = REGISTRY.get_sample_value("fea_queue_depth")
    running = REGISTRY.get_sample_value("fea_running_jobs")
    assert age is not None and age >= 5
    assert depth == 1.0
    assert running == 0.0


def test_manual_review_reason_is_cause_not_verdict(settings):
    before_stale = REGISTRY.get_sample_value("manual_review_total", {"reason": "stale"}) or 0.0
    before_verdict = REGISTRY.get_sample_value("manual_review_total", {"reason": "MANUAL_REVIEW"}) or 0.0
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(
        PRIMARY,
        DEMO,
        source_timestamp=datetime.now(timezone.utc) - timedelta(minutes=10),
        quality="GOOD",
    )
    evaluation.start_operational(PRIMARY)
    after_stale = REGISTRY.get_sample_value("manual_review_total", {"reason": "stale"}) or 0.0
    after_verdict = REGISTRY.get_sample_value("manual_review_total", {"reason": "MANUAL_REVIEW"}) or 0.0
    assert after_stale >= before_stale + 1
    assert after_verdict == before_verdict


def test_bad_quality_manual_review_reason(settings):
    before = REGISTRY.get_sample_value("manual_review_total", {"reason": "bad_quality"}) or 0.0
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="BAD")
    evaluation.start_operational(PRIMARY)
    after = REGISTRY.get_sample_value("manual_review_total", {"reason": "bad_quality"}) or 0.0
    assert after >= before + 1


def test_fea_timeout_manual_review_reason(settings, monkeypatch):
    before = REGISTRY.get_sample_value("manual_review_total", {"reason": "fea_timeout"}) or 0.0

    def boom(*_args, **_kwargs):
        raise SolverError("engine exceeded 1s", "TIMEOUT")

    monkeypatch.setattr("cold_drawing_twin.simulation.run.run_openradioss", boom)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    evaluation.start_operational(PRIMARY)
    after = REGISTRY.get_sample_value("manual_review_total", {"reason": "fea_timeout"}) or 0.0
    assert after >= before + 1


def test_http_metrics_use_route_template_not_resource_ids(settings):
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, _events, _evaluation = container.services(session)
    twin.put_process_state(
        PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD", state_version="state-0001"
    )
    session.commit()
    client = TestClient(create_app(container))
    first = client.post(
        f"/assets/{PRIMARY}/evaluations",
        json={"mode": "OPERATIONAL", "expected_state_version": "state-0001"},
    )
    twin.put_process_state(
        PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD", state_version="state-0002"
    )
    session.commit()
    second = client.post(
        f"/assets/{PRIMARY}/evaluations",
        json={"mode": "OPERATIONAL", "expected_state_version": "state-0002"},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    id_one = first.json()["evaluation_id"]
    id_two = second.json()["evaluation_id"]
    assert id_one != id_two
    labels = {"path": "/evaluations/{evaluation_id}", "method": "GET", "status": "200"}
    before = REGISTRY.get_sample_value("http_requests_total", labels) or 0.0
    assert client.get(f"/evaluations/{id_one}").status_code == 200
    assert client.get(f"/evaluations/{id_two}").status_code == 200
    after = REGISTRY.get_sample_value("http_requests_total", labels) or 0.0
    assert after >= before + 2
    raw_one = REGISTRY.get_sample_value(
        "http_requests_total", {"path": f"/evaluations/{id_one}", "method": "GET", "status": "200"}
    )
    raw_two = REGISTRY.get_sample_value(
        "http_requests_total", {"path": f"/evaluations/{id_two}", "method": "GET", "status": "200"}
    )
    assert raw_one is None
    assert raw_two is None
