from datetime import datetime, timedelta, timezone

from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.persistence.models import DecisionRow, SnapshotRow
from tests.conftest import DEMO, PRIMARY, make_pinn
from cold_drawing_twin.orchestration.container import build_container


def test_e2e_fast_safe(settings):
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert row.state == "FINALIZED"
    assert decision.verdict == "SAFE"
    assert decision.fea_job_id is None
    assert twin.require(PRIMARY).latest_verdict == "SAFE"


def test_e2e_unsafe_no_extra_fea(settings):
    container = build_container(settings=settings, pinn=make_pinn("UNSAFE"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert decision.verdict == "UNSAFE"
    assert decision.fea_job_id is None


def test_e2e_need_fea_goes_to_review_without_calibrated_material(settings, monkeypatch):
    def fake_run_case(features, work_dir, job_id, run_solver=True):
        work_dir.mkdir(parents=True, exist_ok=True)
        return {
            "solver_status": "FAILED",
            "solver_error": "hardening-map-v1 has no calibrated plastic curve",
            "quality_pass": False,
            "quality_reason": "missing histories",
            "criterion_verdict": "INCONCLUSIVE",
            "criterion_reason": "required_thresholds is empty",
            "metrics": {},
            "decks": {},
            "work_dir": str(work_dir),
        }

    monkeypatch.setattr("cold_drawing_twin.orchestration.fea.run_case", fake_run_case)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert decision.status == "MANUAL_REVIEW"
    assert decision.fea_job_id is not None


def test_stale_blocks_automatic_decision(settings):
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(
        PRIMARY,
        DEMO,
        source_timestamp=datetime.now(timezone.utc) - timedelta(minutes=10),
        quality="GOOD",
    )
    row = evaluation.start_operational(PRIMARY)
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert decision.status == "MANUAL_REVIEW"
    assert decision.verdict == "MANUAL_REVIEW"


def test_scenario_does_not_change_live_features(settings):
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(
        PRIMARY,
        DEMO,
        source_timestamp=datetime.now(timezone.utc),
        quality="GOOD",
        state_version="state-live",
    )
    live = evaluation.start_operational(PRIMARY)
    snapshot = session.get(SnapshotRow, live.snapshot_id)
    scenario, _row = evaluation.start_scenario(
        snapshot.snapshot_id,
        {"reduction_ratio": 0.4},
    )
    session.flush()
    current = twin.require(PRIMARY)
    assert current.features["reduction_ratio"] == 0.3
    assert current.state_version == "state-live"
    assert scenario.overrides["reduction_ratio"] == 0.4
