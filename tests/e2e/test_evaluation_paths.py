from datetime import datetime, timedelta, timezone

from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.inference.pinn.adapter import ReleasedPinnAdapter
from cold_drawing_twin.orchestration.container import build_container
from cold_drawing_twin.persistence.models import DecisionRow, FeaJobRow, SnapshotRow
from cold_drawing_twin.simulation.solver.openradioss import SolverError
from tests.conftest import DEMO, PRIMARY, make_pinn


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
    lineage = decision.lineage
    assert lineage["asset_id"] == PRIMARY
    assert lineage["snapshot_id"] == row.snapshot_id
    assert lineage["pinn"]["output"]["verdict"] == "SAFE"
    assert lineage["pinn"]["input"]["reduction_ratio"] == 0.3
    assert lineage["routing"]["action"] == "ACCEPT"
    assert lineage["decision"]["decision_id"] == decision.decision_id
    assert lineage["fea"] is None


def test_e2e_unsafe_no_extra_fea(settings):
    container = build_container(settings=settings, pinn=make_pinn("UNSAFE"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert decision.verdict == "UNSAFE"
    assert decision.fea_job_id is None


def test_e2e_need_fea_inconclusive_without_solver(settings):
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert decision.status == "MANUAL_REVIEW"
    assert decision.verdict == "INCONCLUSIVE"
    assert decision.fea_job_id is not None
    assert decision.lineage["fea"]["job_id"] == decision.fea_job_id


def test_e2e_need_fea_from_released_adapter_out_of_range(settings):
    container = build_container(
        settings=settings,
        pinn=ReleasedPinnAdapter(settings.pinn_model_dir, "v0.1.1"),
    )
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(
        PRIMARY,
        ProcessFeatures(0.55, 0.2, 0.08, 0.7),
        source_timestamp=datetime.now(timezone.utc),
        quality="GOOD",
    )
    row = evaluation.start_operational(PRIMARY)
    assert row.routing_action == "REQUIRES_FEA"
    assert row.pinn_result["verdict"] == "NEED_FEA"
    assert row.pinn_result["supported_range"] is False


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


def test_bad_opcua_quality_blocks_automatic_decision(settings):
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="BAD")
    row = evaluation.start_operational(PRIMARY)
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert decision.status == "MANUAL_REVIEW"


def test_pinn_unavailable_is_manual_review(settings):
    container = build_container(
        settings=settings,
        pinn=ReleasedPinnAdapter(settings.pinn_model_dir, "v0.1.1"),
    )
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert decision.status == "MANUAL_REVIEW"


def test_fea_timeout_is_inconclusive(settings, monkeypatch):
    def boom(*_args, **_kwargs):
        raise SolverError("engine exceeded 1s", "TIMEOUT")

    monkeypatch.setattr("cold_drawing_twin.simulation.run.run_openradioss", boom)
    container = build_container(settings=settings, pinn=make_pinn("NEED_FEA"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    job = session.get(FeaJobRow, decision.fea_job_id)
    assert job.status == "TIMEOUT"
    assert decision.verdict == "INCONCLUSIVE"
    assert decision.status == "MANUAL_REVIEW"


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
