from datetime import datetime, timedelta, timezone

from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.domain.lineage import iso
from cold_drawing_twin.inference.pinn.adapter import ReleasedPinnAdapter
from cold_drawing_twin.orchestration.container import build_container
from cold_drawing_twin.persistence.models import DecisionRow, FeaJobRow, SnapshotRow
from cold_drawing_twin.simulation.solver.openradioss import SolverError
from tests.conftest import DEMO, PRIMARY, make_pinn


def test_e2e_fast_safe(settings):
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    source = datetime.now(timezone.utc) - timedelta(seconds=5)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=source, quality="GOOD")
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
    snapshot = session.get(SnapshotRow, row.snapshot_id)
    twin_row = twin.require(PRIMARY)
    assert lineage["source_timestamp"] == iso(snapshot.source_timestamp)
    assert lineage["source_timestamp"] == iso(twin_row.source_timestamp)
    assert lineage["snapshot"]["source_timestamp"] == iso(twin_row.source_timestamp)
    assert lineage["snapshot"]["captured_at"] == iso(snapshot.captured_at)
    assert lineage["snapshot"]["captured_at"] != lineage["source_timestamp"]
    assert lineage["snapshot"]["source_timestamp_provenance"] == "measurement"
    assert snapshot.source_timestamp_provenance == "measurement"
    assert snapshot.source_quality == "GOOD"
    assert snapshot.input_quality == "MEASURED"
    assert lineage["snapshot"]["source_quality"] == "GOOD"


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
    source = datetime.now(timezone.utc) - timedelta(seconds=5)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=source, quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert decision.status == "MANUAL_REVIEW"
    assert decision.verdict == "INCONCLUSIVE"
    assert decision.fea_job_id is not None
    assert decision.lineage["fea"]["job_id"] == decision.fea_job_id
    snapshot = session.get(SnapshotRow, row.snapshot_id)
    twin_row = twin.require(PRIMARY)
    assert decision.lineage["source_timestamp"] == iso(snapshot.source_timestamp)
    assert decision.lineage["source_timestamp"] == iso(twin_row.source_timestamp)
    assert decision.lineage["snapshot"]["source_timestamp"] == iso(twin_row.source_timestamp)
    assert decision.lineage["snapshot"]["captured_at"] == iso(snapshot.captured_at)
    assert decision.lineage["snapshot"]["captured_at"] != decision.lineage["source_timestamp"]
    assert decision.lineage["snapshot"]["source_timestamp_provenance"] == "measurement"


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
    snapshot = session.get(SnapshotRow, row.snapshot_id)
    assert decision.status == "MANUAL_REVIEW"
    assert snapshot.source_quality == "BAD"
    assert snapshot.input_quality == "MEASURED"
    assert decision.lineage["snapshot"]["source_quality"] == "BAD"


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
        source_timestamp=datetime.now(timezone.utc) - timedelta(seconds=5),
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
    child = session.get(SnapshotRow, _row.snapshot_id)
    assert iso(child.source_timestamp) == iso(snapshot.source_timestamp)
    assert iso(child.source_timestamp) != iso(child.captured_at)
    assert child.source_quality == snapshot.source_quality == "GOOD"
    assert child.input_quality == "SCENARIO_ASSUMED"
    assert snapshot.input_quality == "MEASURED"
    assert current.quality == "GOOD"


def test_scenario_keeps_bad_source_quality_without_rewriting_it(settings):
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="BAD")
    blocked = evaluation.start_operational(PRIMARY)
    base = session.get(SnapshotRow, blocked.snapshot_id)
    live_quality = twin.require(PRIMARY).quality
    scenario, child_row = evaluation.start_scenario(base.snapshot_id, {"reduction_ratio": 0.4})
    child = session.get(SnapshotRow, child_row.snapshot_id)
    current = twin.require(PRIMARY)
    assert base.source_quality == "BAD"
    assert child.source_quality == "BAD"
    assert child.input_quality == "SCENARIO_ASSUMED"
    assert child.source_quality != "GOOD"
    assert current.quality == live_quality == "BAD"
    assert scenario.base_snapshot_id == base.snapshot_id
    assert child_row.routing_action == "ACCEPT"
    assert session.query(DecisionRow).filter_by(evaluation_id=child_row.evaluation_id).one().verdict == "SAFE"
