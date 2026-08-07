from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cold_drawing_twin.api.schemas import EvaluationRequest, ProcessStateBody, ScenarioRequest
from cold_drawing_twin.config_files import asset_registry
from cold_drawing_twin.domain.features import features_from_mapping
from cold_drawing_twin.domain.lineage import iso, utc_now
from cold_drawing_twin.history.store import history_for
from cold_drawing_twin.persistence.models import DecisionRow, EvaluationRow, FeaJobRow, ScenarioRow, SnapshotRow
from cold_drawing_twin.twin.store import TwinStore

router = APIRouter()
LOGGER = logging.getLogger(__name__)


def get_session():
    from cold_drawing_twin.api.app import container

    session = container.open()
    try:
        yield session
        session.commit()
        from cold_drawing_twin.orchestration.fea import dispatch_fea_jobs

        try:
            dispatch_fea_jobs(container.settings)
        except Exception:
            LOGGER.exception("FEA publish after commit failed; unpublished outbox remains for fea-requeue")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def services(session: Session = Depends(get_session)):
    from cold_drawing_twin.api.app import container

    return container.services(session)


@router.get("/assets")
def list_assets():
    registry = asset_registry()
    return {
        "assets": [
            {"asset_id": asset_id, "aas_id": item["aas_id"], "usd_prim": item["usd_prim"], "class": item["class"]}
            for asset_id, item in registry.items()
        ]
    }


@router.get("/assets/{asset_id}")
def get_asset(asset_id: str):
    registry = asset_registry()
    if asset_id not in registry:
        raise HTTPException(404, "unknown asset")
    item = registry[asset_id]
    return {"asset_id": asset_id, "aas_id": item["aas_id"], "usd_prim": item["usd_prim"], "class": item["class"]}


@router.get("/assets/{asset_id}/state")
def get_state(asset_id: str, session: Session = Depends(get_session)):
    twin = TwinStore(session)
    row = twin.get(asset_id)
    if row is None:
        raise HTTPException(404, "asset state is not loaded")
    return {
        "asset_id": row.asset_id,
        "state_version": row.state_version,
        "features": row.features,
        "source_timestamp": iso(row.source_timestamp),
        "ingest_timestamp": iso(row.ingest_timestamp),
        "quality": row.quality,
        "latest_evaluation_id": row.latest_evaluation_id,
        "latest_snapshot_id": row.latest_snapshot_id,
        "latest_verdict": row.latest_verdict,
        "active_fea_job_id": row.active_fea_job_id,
        "last_completed_fea_job_id": row.last_completed_fea_job_id,
    }


@router.put("/assets/{asset_id}/state")
def put_state(asset_id: str, body: ProcessStateBody, session: Session = Depends(get_session)):
    twin = TwinStore(session)
    try:
        row = twin.put_process_state(
            asset_id,
            features_from_mapping(body.model_dump(exclude={"state_version", "quality"})),
            source_timestamp=utc_now(),
            quality=body.quality,
            state_version=body.state_version,
        )
    except KeyError:
        raise HTTPException(404, "unknown asset") from None
    return {"asset_id": asset_id, "state_version": row.state_version}


@router.get("/assets/{asset_id}/history")
def get_history(asset_id: str, session: Session = Depends(get_session)):
    if asset_id not in asset_registry():
        raise HTTPException(404, "unknown asset")
    return {"asset_id": asset_id, "points": history_for(session, asset_id)}


@router.post("/assets/{asset_id}/evaluations")
def post_evaluation(asset_id: str, body: EvaluationRequest, deps=Depends(services), session: Session = Depends(get_session)):
    twin, _events, evaluation = deps
    if twin.get(asset_id) is None:
        raise HTTPException(404, "asset state is not loaded")
    try:
        row = evaluation.start_operational(asset_id, body.expected_state_version)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _evaluation_body(session, row)


@router.get("/evaluations/{evaluation_id}")
def get_evaluation(evaluation_id: str, session: Session = Depends(get_session)):
    row = session.get(EvaluationRow, evaluation_id)
    if row is None:
        raise HTTPException(404, "evaluation not found")
    return _evaluation_body(session, row)


@router.post("/scenarios")
def post_scenario(body: ScenarioRequest, deps=Depends(services), session: Session = Depends(get_session)):
    _twin, _events, evaluation = deps
    try:
        scenario, row = evaluation.start_scenario(body.base_snapshot_id, body.overrides)
    except KeyError:
        raise HTTPException(404, "base snapshot not found") from None
    return {
        "scenario_id": scenario.scenario_id,
        "evaluation_id": row.evaluation_id,
        "base_snapshot_id": scenario.base_snapshot_id,
        "overrides": scenario.overrides,
        "evaluation": _evaluation_body(session, row),
    }


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str, session: Session = Depends(get_session)):
    row = session.get(ScenarioRow, scenario_id)
    if row is None:
        raise HTTPException(404, "scenario not found")
    evaluation = session.get(EvaluationRow, row.evaluation_id)
    return {
        "scenario_id": row.scenario_id,
        "evaluation_id": row.evaluation_id,
        "base_snapshot_id": row.base_snapshot_id,
        "overrides": row.overrides,
        "evaluation": _evaluation_body(session, evaluation) if evaluation else None,
    }


@router.get("/fea-jobs/{job_id}")
def get_fea_job(job_id: str, session: Session = Depends(get_session)):
    row = session.get(FeaJobRow, job_id)
    if row is None:
        raise HTTPException(404, "FEA job not found")
    return {
        "job_id": row.job_id,
        "evaluation_id": row.evaluation_id,
        "snapshot_id": row.snapshot_id,
        "status": row.status,
        "solver": row.solver,
        "solver_version": row.solver_version,
        "material_mapping_version": row.material_mapping_version,
        "safety_criterion_version": row.safety_criterion_version,
        "criterion_verdict": row.criterion_verdict,
        "quality": row.quality,
        "work_dir": row.work_dir,
        "artifacts": row.artifacts,
        "error": row.error,
    }


@router.get("/decisions/{decision_id}")
def get_decision(decision_id: str, session: Session = Depends(get_session)):
    row = session.get(DecisionRow, decision_id)
    if row is None:
        raise HTTPException(404, "decision not found")
    return {
        "decision_id": row.decision_id,
        "evaluation_id": row.evaluation_id,
        "snapshot_id": row.snapshot_id,
        "status": row.status,
        "verdict": row.verdict,
        "model_version": row.model_version,
        "routing_policy_version": row.routing_policy_version,
        "fea_job_id": row.fea_job_id,
        "lineage": row.lineage,
    }


def _evaluation_body(session: Session, row: EvaluationRow) -> dict:
    snapshot = session.get(SnapshotRow, row.snapshot_id)
    decision = (
        session.query(DecisionRow).filter(DecisionRow.evaluation_id == row.evaluation_id).order_by(DecisionRow.created_at.desc()).first()
    )
    job = (
        session.query(FeaJobRow).filter(FeaJobRow.evaluation_id == row.evaluation_id).order_by(FeaJobRow.created_at.desc()).first()
    )
    return {
        "evaluation_id": row.evaluation_id,
        "asset_id": row.asset_id,
        "snapshot_id": row.snapshot_id,
        "scenario_id": row.scenario_id,
        "mode": row.mode,
        "state": row.state,
        "routing_action": row.routing_action,
        "pinn_result": row.pinn_result,
        "snapshot": None
        if snapshot is None
        else {
            "snapshot_id": snapshot.snapshot_id,
            "asset_id": snapshot.asset_id,
            "captured_at": iso(snapshot.captured_at),
            "source_timestamp": iso(snapshot.source_timestamp),
            "source_timestamp_provenance": snapshot.source_timestamp_provenance,
            "ingest_timestamp": iso(snapshot.ingest_timestamp),
            "source_state_version": snapshot.source_state_version,
            "features": snapshot.features,
        },
        "fea_job_id": None if job is None else job.job_id,
        "decision_id": None if decision is None else decision.decision_id,
        "decision": None
        if decision is None
        else {
            "decision_id": decision.decision_id,
            "status": decision.status,
            "verdict": decision.verdict,
            "fea_job_id": decision.fea_job_id,
        },
    }
