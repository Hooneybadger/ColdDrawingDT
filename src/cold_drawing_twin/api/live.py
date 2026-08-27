from __future__ import annotations

from sqlalchemy.orm import Session

from cold_drawing_twin.config_files import asset_registry
from cold_drawing_twin.display import fea_lifecycle_label
from cold_drawing_twin.domain.lineage import iso
from cold_drawing_twin.persistence.models import DecisionRow, EvaluationRow, FeaJobRow
from cold_drawing_twin.twin.store import TwinStore


def _fea_quality_label(job: FeaJobRow | None) -> str | None:
    if job is None or not job.quality:
        return None
    if isinstance(job.quality, dict):
        passed = job.quality.get("pass")
        if passed is True:
            return "PASS"
        if passed is False:
            return "FAIL"
        reason = job.quality.get("reason")
        return str(reason) if reason else None
    return str(job.quality)


def live_view(session: Session, asset_id: str) -> dict:
    """Read-only assembly of Twin, Evaluation, Decision, and FEA for display."""
    registry = asset_registry()
    item = registry[asset_id]
    row = TwinStore(session).get(asset_id)
    base = {
        "asset_id": asset_id,
        "aas_id": item["aas_id"],
        "usd_prim": item["usd_prim"],
        "backend_status": "ONLINE",
    }
    if row is None:
        return {
            **base,
            "process": None,
            "decision": None,
            "fea": {"status": "IDLE", "last_completed_fea_job_id": None},
        }
    evaluation = session.get(EvaluationRow, row.latest_evaluation_id) if row.latest_evaluation_id else None
    decision = session.get(DecisionRow, row.latest_decision_id) if row.latest_decision_id else None
    job_id = row.active_fea_job_id or row.last_completed_fea_job_id
    job = session.get(FeaJobRow, job_id) if job_id else None
    model_version = None
    if evaluation and isinstance(evaluation.pinn_result, dict):
        model_version = evaluation.pinn_result.get("model_version")
    if decision is not None and decision.model_version:
        model_version = decision.model_version
    fea_job_id = row.active_fea_job_id
    if fea_job_id is None and decision is not None:
        fea_job_id = decision.fea_job_id
    return {
        **base,
        "process": {
            "features": row.features,
            "state_version": row.state_version,
            "source_timestamp": iso(row.source_timestamp),
            "quality": row.quality,
        },
        "decision": {
            "latest_verdict": row.latest_verdict,
            "evaluation_id": row.latest_evaluation_id,
            "snapshot_id": row.latest_snapshot_id,
            "decision_id": row.latest_decision_id,
            "routing_action": None if evaluation is None else evaluation.routing_action,
            "model_version": model_version,
            "fea_job_id": fea_job_id,
        },
        "fea": {
            "status": fea_lifecycle_label(None if job is None else job.status, active=bool(row.active_fea_job_id)),
            "job_status": None if job is None else job.status,
            "solver": None if job is None else job.solver,
            "solver_version": None if job is None else job.solver_version,
            "criterion_verdict": None if job is None else job.criterion_verdict,
            "quality": _fea_quality_label(job),
            "last_completed_fea_job_id": row.last_completed_fea_job_id,
        },
    }
