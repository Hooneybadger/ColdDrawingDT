import threading
import time
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from cold_drawing_twin.api.app import create_app
from cold_drawing_twin.orchestration.container import build_container
from cold_drawing_twin.orchestration.fea import (
    claim_queued_fea_job,
    dispatch_fea_jobs,
    pending_fea_job_ids,
    reclaim_expired_running_fea_jobs,
    renew_fea_lease,
    run_fea_job,
)
from cold_drawing_twin.orchestration.outbox import unpublished_outbox_job_ids
from cold_drawing_twin.persistence.models import DecisionRow, FeaJobRow, FeaOutboxRow
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


def test_claim_queued_job_is_single_winner(tmp_path):
    settings = _celery_settings(tmp_path)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    job = session.query(FeaJobRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert job.status == "QUEUED"
    first = claim_queued_fea_job(session, job.job_id)
    second = claim_queued_fea_job(session, job.job_id)
    assert first is not None
    assert first.status == "RUNNING"
    assert second is None
    session.refresh(job)
    assert job.status == "RUNNING"


def test_publish_failure_leaves_queued_and_requeue_republishes(tmp_path, monkeypatch):
    def boom(job_id, priority=False):
        raise RuntimeError("broker down")

    monkeypatch.setattr("workers.fea_tasks.enqueue_fea_job", boom)
    settings = _celery_settings(tmp_path)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    pending = pending_fea_job_ids(session)
    session.commit()
    failed = dispatch_fea_jobs(settings, pending)
    session.expire_all()
    job = session.query(FeaJobRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert job.status == "QUEUED"
    assert failed == pending
    assert unpublished_outbox_job_ids(session) == pending
    recorded: list[str] = []
    monkeypatch.setattr("workers.fea_tasks.enqueue_fea_job", lambda job_id, priority=False: recorded.append(job_id))
    again = dispatch_fea_jobs(settings)
    assert recorded == pending
    assert again == []
    session.expire_all()
    session.refresh(job)
    assert job.status == "QUEUED"
    outbox = session.query(FeaOutboxRow).filter_by(job_id=job.job_id).one()
    assert outbox.published_at is not None


def test_successful_publish_does_not_republish_queued_job(tmp_path, monkeypatch):
    recorded: list[str] = []
    monkeypatch.setattr("workers.fea_tasks.enqueue_fea_job", lambda job_id, priority=False: recorded.append(job_id))
    settings = _celery_settings(tmp_path)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    session.commit()
    assert dispatch_fea_jobs(settings) == []
    first = list(recorded)
    assert first
    assert dispatch_fea_jobs(settings) == []
    assert recorded == first
    job = session.query(FeaJobRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert job.status == "QUEUED"


def test_expired_lease_without_work_dir_returns_to_queued(tmp_path):
    settings = _celery_settings(tmp_path)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    job = session.query(FeaJobRow).filter_by(evaluation_id=row.evaluation_id).one()
    claimed = claim_queued_fea_job(session, job.job_id)
    assert claimed is not None
    claimed.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    session.flush()
    result = reclaim_expired_running_fea_jobs(session, settings, events, twin)
    session.refresh(job)
    assert job.status == "QUEUED"
    assert result["requeued"] == [job.job_id]
    assert unpublished_outbox_job_ids(session) == [job.job_id]


def test_expired_lease_with_work_dir_is_inconclusive(tmp_path):
    settings = _celery_settings(tmp_path)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    job = session.query(FeaJobRow).filter_by(evaluation_id=row.evaluation_id).one()
    claimed = claim_queued_fea_job(session, job.job_id)
    claimed.work_dir = str(tmp_path / "started")
    claimed.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    session.flush()
    result = reclaim_expired_running_fea_jobs(session, settings, events, twin)
    session.refresh(job)
    assert job.status == "TIMEOUT"
    assert result["timed_out"] == [job.job_id]
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert decision.verdict == "INCONCLUSIVE"


def test_lost_lease_drops_late_worker_result(tmp_path, monkeypatch):
    settings = _celery_settings(tmp_path)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    job = session.query(FeaJobRow).filter_by(evaluation_id=row.evaluation_id).one()

    original = run_fea_job.__globals__["run_case"]

    def bump_generation(*args, **kwargs):
        current = session.get(FeaJobRow, job.job_id)
        current.claim_generation = int(current.claim_generation or 0) + 1
        session.flush()
        return original(*args, **kwargs)

    monkeypatch.setattr("cold_drawing_twin.orchestration.fea.run_case", bump_generation)
    again = run_fea_job(session, job.job_id, settings, events, twin)
    assert again.status == "RUNNING"
    assert session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).first() is None


def test_renew_lease_requires_matching_generation(tmp_path):
    settings = _celery_settings(tmp_path)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    job = session.query(FeaJobRow).filter_by(evaluation_id=row.evaluation_id).one()
    claimed = claim_queued_fea_job(session, job.job_id, lease_s=30)
    generation = int(claimed.claim_generation)
    original_expiry = claimed.lease_expires_at
    later = datetime.now(timezone.utc) + timedelta(seconds=10)
    assert renew_fea_lease(session, job.job_id, generation, lease_s=30, now=later) is True
    session.refresh(job)

    def as_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    assert as_utc(job.lease_expires_at) == later + timedelta(seconds=30)
    assert as_utc(job.lease_expires_at) != as_utc(original_expiry)
    job.claim_generation = generation + 1
    session.flush()
    assert renew_fea_lease(session, job.job_id, generation, lease_s=30) is False
    session.refresh(job)
    assert as_utc(job.lease_expires_at) == later + timedelta(seconds=30)


def test_worker_commits_running_before_solver(tmp_path, monkeypatch):
    settings = _celery_settings(tmp_path)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    job = session.query(FeaJobRow).filter_by(evaluation_id=row.evaluation_id).one()
    seen: dict[str, str | None] = {}
    original = run_fea_job.__globals__["run_case"]

    def inspect_run_case(*args, **kwargs):
        other = container.open()
        try:
            visible = other.get(FeaJobRow, job.job_id)
            seen["status"] = visible.status if visible is not None else None
            seen["work_dir"] = visible.work_dir if visible is not None else None
        finally:
            other.close()
        return original(*args, **kwargs)

    monkeypatch.setattr("cold_drawing_twin.orchestration.fea.run_case", inspect_run_case)
    run_fea_job(session, job.job_id, settings, events, twin)
    assert seen["status"] == "RUNNING"
    assert seen["work_dir"]


def test_heartbeat_keeps_live_solver_off_reclaim(tmp_path, monkeypatch):
    settings = _celery_settings(tmp_path)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    job = session.query(FeaJobRow).filter_by(evaluation_id=row.evaluation_id).one()
    seen: dict[str, dict[str, list[str]]] = {}
    renewed = threading.Event()
    original = run_fea_job.__globals__["run_case"]
    real_renew = renew_fea_lease

    def tracking_renew(*args, **kwargs):
        ok = real_renew(*args, **kwargs)
        if ok:
            renewed.set()
        return ok

    def slow_run_case(*args, **kwargs):
        assert renewed.wait(timeout=2.0)
        time.sleep(0.25)
        other = container.open()
        try:
            other_twin, other_events, _evaluation = container.services(other)
            seen["reclaim"] = reclaim_expired_running_fea_jobs(
                other,
                settings,
                other_events,
                other_twin,
                now=datetime.now(timezone.utc) + timedelta(seconds=2.8),
            )
            other.commit()
        finally:
            other.close()
        return original(*args, **kwargs)

    monkeypatch.setattr("cold_drawing_twin.orchestration.fea.renew_fea_lease", tracking_renew)
    monkeypatch.setattr("cold_drawing_twin.orchestration.fea.run_case", slow_run_case)
    finished = run_fea_job(
        session,
        job.job_id,
        settings,
        events,
        twin,
        lease_s=3,
        heartbeat_interval_s=0.08,
    )
    assert seen["reclaim"] == {"requeued": [], "timed_out": []}
    assert finished.status != "TIMEOUT"
