from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter

from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from cold_drawing_twin.config_files import routing_policy
from cold_drawing_twin.domain.features import features_from_mapping
from cold_drawing_twin.domain.lineage import lineage_record, snapshot_payload, utc_now
from cold_drawing_twin.domain.types import (
    DecisionStatus,
    DecisionVerdict,
    EvaluationMode,
    EvaluationState,
    FeaCriterionVerdict,
    FeaJobStatus,
)
from cold_drawing_twin.orchestration.events import EventBus
from cold_drawing_twin.observability.metrics import fea_job_duration_seconds, fea_jobs_total
from cold_drawing_twin.orchestration.evaluation import EvaluationService
from cold_drawing_twin.orchestration.outbox import (
    ensure_unpublished_outbox,
    mark_outbox_published,
    record_outbox_error,
    unpublished_outbox_job_ids,
)
from cold_drawing_twin.domain.timeouts import fea_task_hard_limit_s
from cold_drawing_twin.persistence.models import DecisionRow, EvaluationRow, FeaJobRow, SnapshotRow
from cold_drawing_twin.settings import Settings
from cold_drawing_twin.simulation.run import run_case
from cold_drawing_twin.twin.store import TwinStore

LOGGER = logging.getLogger(__name__)


def pending_fea_job_ids(session: Session) -> list[str]:
    return list(session.info.get("fea_jobs") or [])


def unpublished_queued_fea_job_ids(session: Session) -> list[str]:
    """QUEUED jobs. Prefer unpublished_outbox_job_ids for broker republish."""
    rows = (
        session.query(FeaJobRow)
        .filter(FeaJobRow.status == FeaJobStatus.QUEUED.value)
        .order_by(FeaJobRow.created_at.asc())
        .all()
    )
    return [row.job_id for row in rows]


def dispatch_fea_jobs(settings: Settings, job_ids: list[str] | None = None) -> list[str]:
    """Publish unpublished outbox rows after COMMIT.

    Inline execution runs the solver inside EvaluationService. Celery
    workers must not start before COMMIT or they miss the row.
    """
    if settings.fea_execution != "celery":
        return []
    from workers.fea_tasks import enqueue_fea_job

    from cold_drawing_twin.persistence.models import make_session_factory

    session = make_session_factory(settings.database_url)()
    unpublished: list[str] = []
    try:
        ids = job_ids if job_ids is not None else unpublished_outbox_job_ids(session)
        for job_id in ids:
            try:
                enqueue_fea_job(job_id)
                mark_outbox_published(session, job_id)
                session.commit()
            except Exception as exc:
                LOGGER.exception("failed to publish FEA job %s; outbox stays unpublished", job_id)
                record_outbox_error(session, job_id, str(exc))
                session.commit()
                unpublished.append(job_id)
        return unpublished
    finally:
        session.close()


LEASE_GRACE_S = 60
LEASE_HEARTBEAT_S = 30.0


def _lease_seconds(settings: Settings | None = None) -> int:
    """Initial lease covers the Celery outer budget; heartbeat extends it while RUNNING."""
    if settings is None:
        settings = Settings(_env_file=None)
    return fea_task_hard_limit_s(settings)


def _heartbeat_interval_s(lease_s: int) -> float:
    return min(LEASE_HEARTBEAT_S, max(lease_s / 4.0, 0.05))


def renew_fea_lease(
    session: Session,
    job_id: str,
    generation: int,
    *,
    lease_s: int,
    now: datetime | None = None,
) -> bool:
    """Extend lease_expires_at when this worker still owns the RUNNING row."""
    current = now or utc_now()
    result = session.execute(
        update(FeaJobRow)
        .where(
            FeaJobRow.job_id == job_id,
            FeaJobRow.status == FeaJobStatus.RUNNING.value,
            FeaJobRow.claim_generation == generation,
        )
        .values(
            lease_expires_at=current + timedelta(seconds=lease_s),
            updated_at=current,
        )
    )
    session.flush()
    return result.rowcount == 1


def _lease_heartbeat_loop(
    bind,
    job_id: str,
    generation: int,
    lease_s: int,
    interval_s: float,
    stop: threading.Event,
) -> None:
    factory = sessionmaker(bind=bind, expire_on_commit=False, future=True)
    while True:
        heartbeat = factory()
        try:
            owned = renew_fea_lease(heartbeat, job_id, generation, lease_s=lease_s)
            heartbeat.commit()
            if not owned:
                return
        except Exception:
            LOGGER.exception("FEA lease heartbeat failed for %s", job_id)
            heartbeat.rollback()
        finally:
            heartbeat.close()
        if stop.wait(interval_s):
            return


def claim_queued_fea_job(session: Session, job_id: str, *, lease_s: int | None = None) -> FeaJobRow | None:
    """Atomically take QUEUED -> RUNNING. A second worker gets None."""
    job = session.get(FeaJobRow, job_id)
    if job is None:
        raise KeyError(job_id)
    now = utc_now()
    generation = int(job.claim_generation or 0) + 1
    lease_expires = now + timedelta(seconds=lease_s if lease_s is not None else _lease_seconds())
    result = session.execute(
        update(FeaJobRow)
        .where(FeaJobRow.job_id == job_id, FeaJobRow.status == FeaJobStatus.QUEUED.value)
        .values(
            status=FeaJobStatus.RUNNING.value,
            updated_at=now,
            claim_generation=generation,
            lease_expires_at=lease_expires,
        )
    )
    session.flush()
    session.refresh(job)
    if result.rowcount != 1:
        return None
    return job


def run_fea_job(
    session: Session,
    job_id: str,
    settings: Settings,
    events: EventBus,
    twin: TwinStore,
    *,
    lease_s: int | None = None,
    heartbeat_interval_s: float | None = None,
) -> FeaJobRow:
    lease = lease_s if lease_s is not None else _lease_seconds(settings)
    job = claim_queued_fea_job(session, job_id, lease_s=lease)
    if job is None:
        existing = session.get(FeaJobRow, job_id)
        if existing is None:
            raise KeyError(job_id)
        return existing
    generation = int(job.claim_generation or 0)
    evaluation = session.get(EvaluationRow, job.evaluation_id)
    snapshot = session.get(SnapshotRow, job.snapshot_id)
    if evaluation is None or snapshot is None:
        raise KeyError("evaluation or snapshot missing")
    operational = evaluation.mode == EvaluationMode.OPERATIONAL.value
    evaluation.state = EvaluationState.FEA_RUNNING.value
    evaluation.updated_at = job.updated_at
    events.emit("FEA_JOB_STATE_CHANGED", {"job_id": job.job_id, "status": job.status})
    session.flush()
    fea_jobs_total.labels(FeaJobStatus.RUNNING.value).inc()

    work_dir = Path(settings.openradioss_work_dir) / job.job_id
    job.work_dir = str(work_dir)
    session.flush()
    # Other processes can only see RUNNING / work_dir / the lease after COMMIT.
    # Starter and Engine each use fea_job_timeout_s, so wall time can exceed one lease.
    session.commit()
    interval = heartbeat_interval_s if heartbeat_interval_s is not None else _heartbeat_interval_s(lease)
    stop = threading.Event()
    heartbeat = threading.Thread(
        target=_lease_heartbeat_loop,
        args=(session.get_bind(), job_id, generation, lease, interval, stop),
        name=f"fea-lease-{job_id}",
        daemon=True,
    )
    heartbeat.start()
    features = features_from_mapping(snapshot.features)
    started = perf_counter()
    try:
        result = run_case(features, work_dir, job.job_id, run_solver=True, settings=settings)
    finally:
        stop.set()
        heartbeat.join(timeout=max(1.0, interval + 1.0))
    fea_job_duration_seconds.observe(perf_counter() - started)
    session.refresh(job)
    if int(job.claim_generation or 0) != generation:
        LOGGER.warning("FEA job %s lost its lease; dropping this worker result", job_id)
        return job
    job.metrics = result["metrics"]
    identity = (result.get("metrics") or {}).get("solver_identity") or {}
    if identity.get("version"):
        job.solver_version = str(identity["version"])
    job.quality = {"pass": result["quality_pass"], "reason": result["quality_reason"]}
    job.criterion_verdict = result["criterion_verdict"]
    job.error = result["solver_error"]
    job.artifacts = {
        "work_dir": str(work_dir),
        "result_json": str(work_dir / "result.json"),
        "starter": (result.get("decks") or {}).get("starter"),
        "engine": (result.get("decks") or {}).get("engine"),
    }
    job.updated_at = utc_now()

    solver_status = result["solver_status"]
    if solver_status == "TIMEOUT":
        job.status = FeaJobStatus.TIMEOUT.value
    elif solver_status != "SUCCEEDED":
        job.status = FeaJobStatus.FAILED.value
    else:
        job.status = FeaJobStatus.SUCCEEDED.value

    fea_jobs_total.labels(job.status).inc()
    events.emit("FEA_JOB_STATE_CHANGED", {"job_id": job.job_id, "status": job.status})

    if job.status in {FeaJobStatus.FAILED.value, FeaJobStatus.TIMEOUT.value}:
        _finalize_from_fea(
            session,
            evaluation,
            snapshot,
            job,
            DecisionVerdict.INCONCLUSIVE,
            DecisionStatus.MANUAL_REVIEW,
            EvaluationState.MANUAL_REVIEW,
            twin,
            events,
            operational,
        )
        return job

    evaluation.state = EvaluationState.POSTPROCESSING.value
    evaluation.updated_at = utc_now()
    events.emit("EVALUATION_STATE_CHANGED", {"evaluation_id": evaluation.evaluation_id, "state": evaluation.state})

    criterion = FeaCriterionVerdict(result["criterion_verdict"])
    if criterion in {FeaCriterionVerdict.INCONCLUSIVE} or not result["quality_pass"]:
        verdict = DecisionVerdict.INCONCLUSIVE
        status = DecisionStatus.MANUAL_REVIEW
        eval_state = EvaluationState.MANUAL_REVIEW
    elif criterion == FeaCriterionVerdict.SAFE:
        verdict = DecisionVerdict.SAFE
        status = DecisionStatus.FINALIZED
        eval_state = EvaluationState.FINALIZED
    else:
        verdict = DecisionVerdict.UNSAFE
        status = DecisionStatus.FINALIZED
        eval_state = EvaluationState.FINALIZED

    _finalize_from_fea(
        session,
        evaluation,
        snapshot,
        job,
        verdict,
        status,
        eval_state,
        twin,
        events,
        operational,
    )
    return job


def _finalize_from_fea(
    session: Session,
    evaluation: EvaluationRow,
    snapshot: SnapshotRow,
    job: FeaJobRow,
    verdict: DecisionVerdict,
    status: DecisionStatus,
    eval_state: EvaluationState,
    twin: TwinStore,
    events: EventBus,
    operational: bool,
) -> None:
    service = EvaluationService(session, twin, pinn=None, events=events)
    lineage = lineage_record(
        asset_id=evaluation.asset_id,
        state_version=snapshot.source_state_version,
        source_timestamp=snapshot.source_timestamp,
        snapshot=snapshot_payload(snapshot),
        pinn=evaluation.pinn_result,
        pinn_input=snapshot.features,
        routing_policy_version=routing_policy()["version"],
        routing_action=evaluation.routing_action or "REQUIRES_FEA",
        fea={
            "job_id": job.job_id,
            "status": job.status,
            "solver": job.solver,
            "solver_version": job.solver_version,
            "material_mapping_version": job.material_mapping_version,
            "material_profile_version": (job.metrics or {}).get("material_profile_version"),
            "mesh_config_version": job.mesh_config_version,
            "fea_profile_version": job.fea_profile_version,
            "safety_criterion_version": job.safety_criterion_version,
            "criterion_verdict": job.criterion_verdict,
            "quality": job.quality,
            "metrics": job.metrics,
        },
    )
    evaluation.state = EvaluationState.FINALIZING.value
    service._finalize(
        evaluation,
        snapshot,
        verdict,
        status,
        (evaluation.pinn_result or {}).get("model_version") or "v0.1.1",
        routing_policy()["version"],
        job.job_id,
        lineage,
        operational,
    )
    evaluation.state = eval_state.value
    job.status = FeaJobStatus.FINALIZED.value if job.status == FeaJobStatus.SUCCEEDED.value else job.status
    job.updated_at = utc_now()
    twin.record_fea_job(evaluation.asset_id, job.job_id, active=False, operational=operational)
    session.flush()


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def timeout_running_fea_job(
    session: Session,
    job: FeaJobRow,
    events: EventBus,
    twin: TwinStore,
    *,
    error: str,
    now: datetime | None = None,
) -> bool:
    """TIMEOUT / INCONCLUSIVE / MANUAL_REVIEW. Does not write SAFE or a second Decision."""
    existing = session.query(DecisionRow).filter(DecisionRow.evaluation_id == job.evaluation_id).first()
    if existing is not None:
        return False
    current = now or utc_now()
    job.claim_generation = int(job.claim_generation or 0) + 1
    job.lease_expires_at = None
    job.status = FeaJobStatus.TIMEOUT.value
    job.error = error
    job.updated_at = current
    evaluation = session.get(EvaluationRow, job.evaluation_id)
    snapshot = session.get(SnapshotRow, job.snapshot_id)
    if evaluation is None or snapshot is None:
        session.flush()
        return True
    operational = evaluation.mode == EvaluationMode.OPERATIONAL.value
    _finalize_from_fea(
        session,
        evaluation,
        snapshot,
        job,
        DecisionVerdict.INCONCLUSIVE,
        DecisionStatus.MANUAL_REVIEW,
        EvaluationState.MANUAL_REVIEW,
        twin,
        events,
        operational,
    )
    session.flush()
    return True


def _lease_expired(job: FeaJobRow, now: datetime, timeout_s: int) -> bool:
    expires = _as_utc(job.lease_expires_at)
    if expires is not None:
        return expires <= now
    updated = _as_utc(job.updated_at)
    if updated is None:
        return True
    return (now - updated).total_seconds() > timeout_s + LEASE_GRACE_S


def reclaim_expired_running_fea_jobs(
    session: Session,
    settings: Settings,
    events: EventBus,
    twin: TwinStore,
    *,
    now: datetime | None = None,
) -> dict[str, list[str]]:
    """Recover RUNNING jobs whose lease expired. Does not invent a solver result."""
    current = now or utc_now()
    timeout_s = fea_task_hard_limit_s(settings)
    running = session.query(FeaJobRow).filter(FeaJobRow.status == FeaJobStatus.RUNNING.value).all()
    requeued: list[str] = []
    timed_out: list[str] = []
    for job in running:
        if not _lease_expired(job, current, timeout_s):
            continue
        if not job.work_dir:
            job.claim_generation = int(job.claim_generation or 0) + 1
            job.lease_expires_at = None
            job.status = FeaJobStatus.QUEUED.value
            job.updated_at = current
            ensure_unpublished_outbox(session, job.job_id, force_new=True)
            requeued.append(job.job_id)
            continue
        timeout_running_fea_job(
            session,
            job,
            events,
            twin,
            error="lease expired while RUNNING",
            now=current,
        )
        timed_out.append(job.job_id)
    session.flush()
    return {"requeued": requeued, "timed_out": timed_out}
