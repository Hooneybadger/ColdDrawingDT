from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter

from sqlalchemy import update
from sqlalchemy.orm import Session

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
from cold_drawing_twin.persistence.models import EvaluationRow, FeaJobRow, SnapshotRow
from cold_drawing_twin.settings import Settings
from cold_drawing_twin.simulation.run import run_case
from cold_drawing_twin.twin.store import TwinStore

LOGGER = logging.getLogger(__name__)


def pending_fea_job_ids(session: Session) -> list[str]:
    return list(session.info.get("fea_jobs") or [])


def unpublished_queued_fea_job_ids(session: Session) -> list[str]:
    rows = (
        session.query(FeaJobRow)
        .filter(FeaJobRow.status == FeaJobStatus.QUEUED.value)
        .order_by(FeaJobRow.created_at.asc())
        .all()
    )
    return [row.job_id for row in rows]


def dispatch_fea_jobs(settings: Settings, job_ids: list[str]) -> list[str]:
    """Publish FEA jobs only after the job row is committed.

    Inline execution runs the solver inside EvaluationService. Celery
    workers must not start before COMMIT or they miss the row.
    Broker publish failure leaves the row QUEUED; use fea-requeue.
    """
    unpublished: list[str] = []
    if settings.fea_execution != "celery" or not job_ids:
        return unpublished
    from workers.fea_tasks import enqueue_fea_job

    for job_id in job_ids:
        try:
            enqueue_fea_job(job_id)
        except Exception:
            LOGGER.exception("failed to publish FEA job %s; row stays QUEUED", job_id)
            unpublished.append(job_id)
    return unpublished


def claim_queued_fea_job(session: Session, job_id: str) -> FeaJobRow | None:
    """Atomically take QUEUED -> RUNNING. A second worker gets None."""
    job = session.get(FeaJobRow, job_id)
    if job is None:
        raise KeyError(job_id)
    now = utc_now()
    result = session.execute(
        update(FeaJobRow)
        .where(FeaJobRow.job_id == job_id, FeaJobRow.status == FeaJobStatus.QUEUED.value)
        .values(status=FeaJobStatus.RUNNING.value, updated_at=now)
    )
    session.flush()
    session.refresh(job)
    if result.rowcount != 1:
        return None
    return job


def run_fea_job(session: Session, job_id: str, settings: Settings, events: EventBus, twin: TwinStore) -> FeaJobRow:
    job = claim_queued_fea_job(session, job_id)
    if job is None:
        existing = session.get(FeaJobRow, job_id)
        if existing is None:
            raise KeyError(job_id)
        return existing
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
    features = features_from_mapping(snapshot.features)
    started = perf_counter()
    result = run_case(features, work_dir, job.job_id, run_solver=True, settings=settings)
    fea_job_duration_seconds.observe(perf_counter() - started)
    job.metrics = result["metrics"]
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
