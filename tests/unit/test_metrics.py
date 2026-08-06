from datetime import datetime, timezone

from prometheus_client import REGISTRY

from cold_drawing_twin.orchestration.container import build_container
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
