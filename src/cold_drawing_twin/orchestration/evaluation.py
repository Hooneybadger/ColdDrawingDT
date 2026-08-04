from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session

from cold_drawing_twin.config_files import fea_criterion, fea_reference, routing_policy, site_policy
from cold_drawing_twin.domain.features import ProcessFeatures, features_from_mapping, in_supported_range
from cold_drawing_twin.domain.freshness import is_stale, missing_required
from cold_drawing_twin.domain.ids import new_id
from cold_drawing_twin.domain.lineage import idempotency_hash, iso, lineage_record, utc_now
from cold_drawing_twin.domain.routing import PinnResult, route
from cold_drawing_twin.domain.types import (
    DecisionStatus,
    DecisionVerdict,
    EvaluationMode,
    EvaluationState,
    FeaJobStatus,
    RoutingAction,
)
from cold_drawing_twin.inference.pinn.adapter import PinnUnavailable
from cold_drawing_twin.orchestration.events import EventBus
from cold_drawing_twin.persistence.models import DecisionRow, EvaluationRow, FeaJobRow, ScenarioRow, SnapshotRow
from cold_drawing_twin.twin.store import TwinStore

Enqueue = Callable[[str], None]


class EvaluationService:
    def __init__(
        self,
        session: Session,
        twin: TwinStore,
        pinn,
        events: EventBus,
        enqueue_fea: Enqueue | None = None,
        now: Callable[[], datetime] | None = None,
        defer_enqueue: bool = False,
    ) -> None:
        self.session = session
        self.twin = twin
        self.pinn = pinn
        self.events = events
        self.enqueue_fea = enqueue_fea
        self.now = now or utc_now
        self.defer_enqueue = defer_enqueue
        self.queued_fea_ids: list[str] = []

    def start_operational(self, asset_id: str, expected_state_version: str | None = None) -> EvaluationRow:
        row = self.twin.require(asset_id)
        if expected_state_version and row.state_version != expected_state_version:
            raise ValueError("expected_state_version does not match live Digital Twin")
        features = features_from_mapping(row.features)
        return self._run(
            asset_id=asset_id,
            features=features,
            source_state_version=row.state_version,
            source_timestamp=row.source_timestamp,
            mode=EvaluationMode.OPERATIONAL,
            operational=True,
            quality=row.quality,
        )

    def start_scenario(self, base_snapshot_id: str, overrides: dict[str, float]) -> tuple[ScenarioRow, EvaluationRow]:
        base = self.session.get(SnapshotRow, base_snapshot_id)
        if base is None:
            raise KeyError(base_snapshot_id)
        merged = dict(base.features)
        merged.update(overrides)
        features = features_from_mapping(merged)
        evaluation = self._run(
            asset_id=base.asset_id,
            features=features,
            source_state_version=base.source_state_version,
            source_timestamp=base.captured_at,
            mode=EvaluationMode.SCENARIO,
            operational=False,
            quality="GOOD",
        )
        scenario = ScenarioRow(
            scenario_id=new_id("scn"),
            base_snapshot_id=base_snapshot_id,
            evaluation_id=evaluation.evaluation_id,
            overrides=overrides,
            created_at=self.now(),
        )
        evaluation.scenario_id = scenario.scenario_id
        self.session.add(scenario)
        self.session.flush()
        return scenario, evaluation

    def _run(
        self,
        *,
        asset_id: str,
        features: ProcessFeatures,
        source_state_version: str,
        source_timestamp: datetime,
        mode: EvaluationMode,
        operational: bool,
        quality: str,
    ) -> EvaluationRow:
        now = self.now()
        snapshot = SnapshotRow(
            snapshot_id=new_id("snap"),
            asset_id=asset_id,
            captured_at=now,
            source_state_version=source_state_version,
            features=features.as_dict(),
            mode=mode.value,
        )
        evaluation = EvaluationRow(
            evaluation_id=new_id("eval"),
            asset_id=asset_id,
            snapshot_id=snapshot.snapshot_id,
            mode=mode.value,
            state=EvaluationState.CREATED.value,
            created_at=now,
            updated_at=now,
        )
        self.session.add_all([snapshot, evaluation])
        evaluation.state = EvaluationState.SNAPSHOT_READY.value
        self.events.emit("EVALUATION_STATE_CHANGED", {"evaluation_id": evaluation.evaluation_id, "state": evaluation.state})

        missing = missing_required(features) or quality != "GOOD"
        stale = is_stale(source_timestamp, now=now)
        pinn_result: PinnResult | None = None
        pinn_invalid = False
        if not missing and not stale:
            evaluation.state = EvaluationState.PINN_RUNNING.value
            evaluation.updated_at = now
            self.events.emit("EVALUATION_STATE_CHANGED", {"evaluation_id": evaluation.evaluation_id, "state": evaluation.state})
            if not in_supported_range(features):
                try:
                    pinn_result = self.pinn.predict(features)
                except PinnUnavailable:
                    pinn_invalid = True
            else:
                try:
                    pinn_result = self.pinn.predict(features)
                except PinnUnavailable:
                    pinn_invalid = True
            if pinn_result is not None:
                evaluation.pinn_result = {
                    "verdict": pinn_result.verdict,
                    "stress_indicator": pinn_result.stress_indicator,
                    "damage_indicator": pinn_result.damage_indicator,
                    "physics_residual": pinn_result.physics_residual,
                    "confidence": None,
                    "model_version": pinn_result.model_version,
                    "supported_range": pinn_result.supported_range,
                }
                if pinn_result.verdict not in {"SAFE", "UNSAFE", "NEED_FEA"}:
                    pinn_invalid = True
        else:
            pinn_invalid = True

        evaluation.state = EvaluationState.ROUTING.value
        policy = site_policy()
        action = route(
            required_input_missing=missing,
            twin_stale=stale,
            pinn_result=pinn_result,
            pinn_invalid=pinn_invalid or pinn_result is None,
            site_requires_fea=bool(policy.get("require_fea")),
        )
        evaluation.routing_action = action.value
        model_version = pinn_result.model_version if pinn_result else "unavailable"
        routing_version = routing_policy()["version"]
        snapshot_payload = {
            "snapshot_id": snapshot.snapshot_id,
            "asset_id": snapshot.asset_id,
            "captured_at": iso(snapshot.captured_at),
            "source_state_version": snapshot.source_state_version,
            "source_timestamp": iso(source_timestamp),
            "features": snapshot.features,
        }
        lineage = lineage_record(
            asset_id=asset_id,
            state_version=source_state_version,
            source_timestamp=source_timestamp,
            snapshot=snapshot_payload,
            pinn=evaluation.pinn_result,
            pinn_input=features.as_dict(),
            routing_policy_version=routing_version,
            routing_action=action.value,
        )

        if action == RoutingAction.ACCEPT:
            self._finalize(
                evaluation,
                snapshot,
                DecisionVerdict.SAFE,
                DecisionStatus.FINALIZED,
                model_version,
                routing_version,
                None,
                lineage,
                operational,
            )
        elif action == RoutingAction.REJECT:
            self._finalize(
                evaluation,
                snapshot,
                DecisionVerdict.UNSAFE,
                DecisionStatus.FINALIZED,
                model_version,
                routing_version,
                None,
                lineage,
                operational,
            )
        elif action == RoutingAction.MANUAL_REVIEW:
            self._finalize(
                evaluation,
                snapshot,
                DecisionVerdict.MANUAL_REVIEW,
                DecisionStatus.MANUAL_REVIEW,
                model_version,
                routing_version,
                None,
                lineage,
                operational,
            )
            evaluation.state = EvaluationState.MANUAL_REVIEW.value
        elif action == RoutingAction.REQUIRES_FEA:
            job = self._queue_fea(evaluation, snapshot, operational)
            evaluation.state = EvaluationState.FEA_QUEUED.value
            evaluation.updated_at = self.now()
            self.events.emit(
                "FEA_JOB_STATE_CHANGED",
                {"job_id": job.job_id, "status": job.status, "evaluation_id": evaluation.evaluation_id},
            )
            if self.enqueue_fea:
                if self.defer_enqueue:
                    self.queued_fea_ids.append(job.job_id)
                    self.session.info.setdefault("fea_jobs", []).append(job.job_id)
                else:
                    self.enqueue_fea(job.job_id)
        self.session.flush()
        return evaluation

    def _queue_fea(self, evaluation: EvaluationRow, snapshot: SnapshotRow, operational: bool) -> FeaJobRow:
        reference = fea_reference()
        criterion = fea_criterion()
        key = idempotency_hash(
            snapshot.snapshot_id,
            reference["version"],
            reference["material"]["mapping_version"],
            reference["mesh"]["profile_version"],
            "unset",
            criterion["version"],
        )
        existing = (
            self.session.query(FeaJobRow)
            .filter(
                FeaJobRow.idempotency_key == key,
                FeaJobRow.status.in_(
                    (
                        FeaJobStatus.QUEUED.value,
                        FeaJobStatus.RUNNING.value,
                        FeaJobStatus.POSTPROCESSING.value,
                    )
                ),
            )
            .order_by(FeaJobRow.created_at.desc())
            .first()
        )
        if existing is not None:
            return existing
        job = FeaJobRow(
            job_id=new_id("fea"),
            evaluation_id=evaluation.evaluation_id,
            snapshot_id=snapshot.snapshot_id,
            status=FeaJobStatus.QUEUED.value,
            solver="OpenRadioss",
            solver_version="unset",
            material_mapping_version=reference["material"]["mapping_version"],
            mesh_config_version=reference["mesh"]["profile_version"],
            fea_profile_version=reference["version"],
            safety_criterion_version=criterion["version"],
            idempotency_key=key,
            created_at=self.now(),
            updated_at=self.now(),
        )
        self.session.add(job)
        self.twin.record_fea_job(evaluation.asset_id, job.job_id, active=True, operational=operational)
        self.session.flush()
        return job

    def _finalize(
        self,
        evaluation: EvaluationRow,
        snapshot: SnapshotRow,
        verdict: DecisionVerdict,
        status: DecisionStatus,
        model_version: str,
        routing_version: str,
        fea_job_id: str | None,
        lineage: dict,
        operational: bool,
    ) -> DecisionRow:
        decision = DecisionRow(
            decision_id=new_id("dec"),
            evaluation_id=evaluation.evaluation_id,
            snapshot_id=snapshot.snapshot_id,
            status=status.value,
            verdict=verdict.value,
            model_version=model_version,
            routing_policy_version=routing_version,
            fea_job_id=fea_job_id,
            lineage=lineage,
            created_at=self.now(),
        )
        self.session.add(decision)
        lineage["decision"] = {
            "decision_id": decision.decision_id,
            "verdict": decision.verdict,
            "status": decision.status,
            "timestamp": iso(decision.created_at),
        }
        decision.lineage = lineage
        evaluation.state = (
            EvaluationState.MANUAL_REVIEW.value
            if status == DecisionStatus.MANUAL_REVIEW
            else EvaluationState.FINALIZED.value
        )
        evaluation.updated_at = self.now()
        self.twin.record_evaluation(
            evaluation.asset_id,
            evaluation_id=evaluation.evaluation_id,
            snapshot_id=snapshot.snapshot_id,
            decision_id=decision.decision_id,
            verdict=verdict.value,
            operational=operational,
        )
        self.events.emit(
            "DECISION_FINALIZED",
            {
                "decision_id": decision.decision_id,
                "evaluation_id": evaluation.evaluation_id,
                "verdict": verdict.value,
                "status": status.value,
            },
        )
        self.session.flush()
        return decision
