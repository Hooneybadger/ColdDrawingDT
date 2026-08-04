from datetime import datetime, timezone

from fastapi.testclient import TestClient

from cold_drawing_twin.api.app import create_app
from cold_drawing_twin.orchestration.container import build_container
from cold_drawing_twin.orchestration.fea import dispatch_fea_jobs, pending_fea_job_ids, run_fea_job
from cold_drawing_twin.persistence.models import DecisionRow, FeaJobRow
from cold_drawing_twin.settings import Settings
from tests.conftest import DEMO, PRIMARY, make_pinn


def _celery_settings(tmp_path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'celery.db'}",
        fea_execution="celery",
        basyx_enabled=False,
        openradioss_work_dir=tmp_path / "fea",
        openradioss_starter_bin="",
        openradioss_engine_bin="",
        pinn_model_dir=tmp_path / "missing-pinn",
        _env_file=None,
    )


def test_celery_defers_solver_until_commit(tmp_path, monkeypatch):
    recorded: list[str] = []
    monkeypatch.setattr("workers.fea_tasks.enqueue_fea_job", lambda job_id, priority=False: recorded.append(job_id))
    settings = _celery_settings(tmp_path)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    assert row.state == "FEA_QUEUED"
    assert session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).first() is None
    assert recorded == []
    pending = pending_fea_job_ids(session)
    session.commit()
    dispatch_fea_jobs(settings, pending)
    assert recorded == pending
    assert recorded


def test_inline_still_finalizes_inside_start_operational(settings):
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert decision.verdict == "INCONCLUSIVE"
    job = session.get(FeaJobRow, decision.fea_job_id)
    assert job.artifacts is not None
    assert job.artifacts["result_json"].endswith("result.json")


def test_worker_skips_job_that_is_not_queued(settings):
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    job = session.query(FeaJobRow).filter_by(evaluation_id=row.evaluation_id).one()
    before = job.status
    assert before != "QUEUED"
    again = run_fea_job(session, job.job_id, settings, events, twin)
    assert again.status == before


def test_http_need_fea_returns_queued_when_celery(tmp_path, monkeypatch):
    recorded: list[str] = []
    monkeypatch.setattr("workers.fea_tasks.enqueue_fea_job", lambda job_id, priority=False: recorded.append(job_id))
    settings = _celery_settings(tmp_path)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, _events, _evaluation = container.services(session)
    twin.put_process_state(
        PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD", state_version="state-0001"
    )
    session.commit()
    client = TestClient(create_app(container))
    posted = client.post(
        f"/assets/{PRIMARY}/evaluations",
        json={"mode": "OPERATIONAL", "expected_state_version": "state-0001"},
    )
    assert posted.status_code == 200
    body = posted.json()
    assert body["state"] == "FEA_QUEUED"
    assert body["decision"] is None
    assert body["fea_job_id"]
    assert recorded == [body["fea_job_id"]]
    job = client.get(f"/fea-jobs/{body['fea_job_id']}").json()
    assert job["status"] == "QUEUED"
    assert job["work_dir"] is None
