import os

import pytest

from cold_drawing_twin.twin.basyx import BasyxClient, submodel_id


@pytest.mark.integration
def test_basyx_process_state_roundtrip():
    if os.environ.get("BASYX_INTEGRATION") != "1":
        pytest.skip("set BASYX_INTEGRATION=1 against a running AAS Environment")
    client = BasyxClient(os.environ.get("BASYX_AAS_REPOSITORY_URL", "http://localhost:8081"), enabled=True)
    state = {
        "features": {
            "reduction_ratio": 0.3,
            "die_half_angle_rad": 0.2,
            "friction_coefficient": 0.08,
            "normalized_hardening_coefficient": 0.7,
        },
        "quality": "GOOD",
        "state_version": "state-basyx",
        "latest_verdict": "SAFE",
        "latest_evaluation_id": "eval-basyx",
        "latest_snapshot_id": "snap-basyx",
        "latest_decision_id": "dec-basyx",
    }
    client.upsert_asset("BG.MIEUM.DRW.04", state)
    aas_id = "urn:bg:mieum:drw:04"
    payload = client.get_submodel(submodel_id(aas_id, "ProcessState"))
    names = {item["idShort"]: item.get("value") for item in payload.get("submodelElements", [])}
    assert float(names["reductionRatio"]) == pytest.approx(0.3)
    evaluation = client.get_submodel(submodel_id(aas_id, "EvaluationState"))
    verdicts = {item["idShort"]: item.get("value") for item in evaluation.get("submodelElements", [])}
    assert verdicts["latestVerdict"] == "SAFE"
