"""In-domain released PINN. Missing files fail; they do not skip as success."""

from datetime import datetime, timezone

import pytest

from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.inference.pinn.adapter import ReleasedPinnAdapter
from cold_drawing_twin.orchestration.container import build_container
from cold_drawing_twin.paths import REPO_ROOT
from cold_drawing_twin.persistence.models import DecisionRow
from cold_drawing_twin.settings import Settings
from tests.conftest import PRIMARY

DEMO = ProcessFeatures(0.3, 0.2, 0.08, 0.7)
BUNDLE = REPO_ROOT / "models" / "cold-drawing-pinn-poc"


def _require_released_bundle() -> None:
    entry = BUNDLE / "predict.py"
    weights = BUNDLE / "pinn.pt"
    if not entry.exists() or not weights.exists():
        pytest.fail(
            f"released PINN bundle missing under {BUNDLE} "
            "(need predict.py and pinn.pt). Run `make fetch-pinn`. "
            "This workflow must not skip as success."
        )


@pytest.mark.pinn_release
def test_released_adapter_runs_predict_py_in_domain():
    _require_released_bundle()
    adapter = ReleasedPinnAdapter(BUNDLE, "v0.1.1")
    result = adapter.predict(DEMO)
    assert result.supported_range is True
    assert result.verdict in {"SAFE", "UNSAFE", "NEED_FEA"}
    assert result.raw.get("decision") == result.verdict
    assert "OUTSIDE_MODEL_DOMAIN" not in (result.raw.get("reason_codes") or [])
    assert result.stress_indicator is not None
    assert result.physics_residual is not None


@pytest.mark.pinn_release
def test_snapshot_released_pinn_routing_decision(tmp_path):
    _require_released_bundle()
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'pinn-release.db'}",
        fea_execution="inline",
        basyx_enabled=False,
        openradioss_work_dir=tmp_path / "fea",
        openradioss_starter_bin="",
        openradioss_engine_bin="",
        pinn_model_dir=BUNDLE,
        _env_file=None,
    )
    container = build_container(settings=settings)
    session = container.open()
    twin, _events, evaluation = container.services(session)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=datetime.now(timezone.utc), quality="GOOD")
    row = evaluation.start_operational(PRIMARY)
    decision = session.query(DecisionRow).filter_by(evaluation_id=row.evaluation_id).one()
    assert row.pinn_result is not None
    assert row.pinn_result["supported_range"] is True
    assert row.pinn_result["verdict"] in {"SAFE", "UNSAFE", "NEED_FEA"}
    assert row.pinn_result["model_version"] == "v0.1.1"
    if row.pinn_result["verdict"] == "SAFE":
        assert row.routing_action == "ACCEPT"
        assert decision.verdict == "SAFE"
        assert decision.fea_job_id is None
    elif row.pinn_result["verdict"] == "UNSAFE":
        assert row.routing_action == "REJECT"
        assert decision.verdict == "UNSAFE"
        assert decision.fea_job_id is None
    else:
        assert row.routing_action == "REQUIRES_FEA"
        assert decision.fea_job_id is not None
