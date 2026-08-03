from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from cold_drawing_twin.config_files import routing_policy
from cold_drawing_twin.domain.features import features_from_mapping
from cold_drawing_twin.domain.lineage import lineage_record, utc_now
from cold_drawing_twin.domain.types import (
    DecisionStatus,
    DecisionVerdict,
    EvaluationMode,
    EvaluationState,
    FeaCriterionVerdict,
    FeaJobStatus,
)
from cold_drawing_twin.orchestration.events import EventBus
from cold_drawing_twin.orchestration.evaluation import EvaluationService
from cold_drawing_twin.persistence.models import EvaluationRow, FeaJobRow, SnapshotRow
from cold_drawing_twin.settings import Settings
from cold_drawing_twin.simulation.run import run_case
from cold_drawing_twin.twin.store import TwinStore


def run_fea_job(session: Session, job_id: str, settings: Settings, events: EventBus, twin: TwinStore) -> FeaJobRow:
    job = session.get(FeaJobRow, job_id)
    if job is None:
        raise KeyError(job_id)
    evaluation = session.get(EvaluationRow, job.evaluation_id)
    snapshot = session.get(SnapshotRow, job.snapshot_id)
    if evaluation is None or snapshot is None:
        raise KeyError("evaluation or snapshot missing")
    operational = evaluation.mode == EvaluationMode.OPERATIONAL.value
    job.status = FeaJobStatus.RUNNING.value
    job.updated_at = utc_now()
    evaluation.state = EvaluationState.FEA_RUNNING.value
    evaluation.updated_at = job.updated_at
    events.emit("FEA_JOB_STATE_CHANGED", {"job_id": job.job_id, "status": job.status})
    session.flush()

    work_dir = Path(settings.openradioss_work_dir) / job.job_id
    job.work_dir = str(work_dir)
    features = features_from_mapping(snapshot.features)
    result = run_case(features, work_dir, job.job_id, run_solver=True, settings=settings)
    job.metrics = result["metrics"]
    job.quality = {"pass": result["quality_pass"], "reason": result["quality_reason"]}
    job.criterion_verdict = result["criterion_verdict"]
    job.error = result["solver_error"]
    job.updated_at = utc_now()

    solver_status = result["solver_status"]
    if solver_status == "TIMEOUT":
        job.status = FeaJobStatus.TIMEOUT.value
    elif solver_status != "SUCCEEDED":
        job.status = FeaJobStatus.FAILED.value
    else:
        job.status = FeaJobStatus.SUCCEEDED.value

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
        source_timestamp=snapshot.captured_at,
        snapshot={
            "snapshot_id": snapshot.snapshot_id,
            "asset_id": snapshot.asset_id,
            "features": snapshot.features,
            "source_state_version": snapshot.source_state_version,
        },
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
