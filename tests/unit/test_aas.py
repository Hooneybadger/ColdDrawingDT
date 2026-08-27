from cold_drawing_twin.twin.basyx import (
    drawing_aas_shell,
    encode_id,
    evaluation_submodel,
    process_submodel,
    read_projected_view,
    simulation_submodel,
    submodel_id,
)
from tests.conftest import PRIMARY


def test_base64url_is_unpadded():
    encoded = encode_id("urn:bg:mieum:drw:04")
    assert "=" not in encoded
    assert encode_id("abc") == "YWJj"


def test_aas_v3_submodels_use_camel_case_id_shorts():
    state = {
        "features": {
            "reduction_ratio": 0.3,
            "die_half_angle_rad": 0.2,
            "friction_coefficient": 0.08,
            "normalized_hardening_coefficient": 0.7,
        },
        "pass_index": 1,
        "quality": "GOOD",
        "state_version": "state-0001",
        "latest_evaluation_id": "eval-1",
        "latest_snapshot_id": "snap-1",
        "latest_decision_id": "dec-1",
        "latest_verdict": "SAFE",
        "active_fea_job_id": None,
        "last_completed_fea_job_id": "fea-1",
    }
    aas_id = "urn:bg:mieum:drw:04"
    shell = drawing_aas_shell("BG.MIEUM.DRW.04")
    assert shell["modelType"] == "AssetAdministrationShell"
    assert "processState" not in shell
    process = process_submodel(aas_id, state)
    evaluation = evaluation_submodel(aas_id, state)
    simulation = simulation_submodel(aas_id, state)
    process_names = [item["idShort"] for item in process["submodelElements"]]
    assert process_names == [
        "reductionRatio",
        "dieHalfAngleRad",
        "frictionCoefficient",
        "normalizedHardeningCoefficient",
        "passIndex",
        "sourceTimestamp",
        "quality",
        "stateVersion",
    ]
    assert [item["idShort"] for item in evaluation["submodelElements"]] == [
        "latestEvaluationId",
        "latestSnapshotId",
        "latestDecisionId",
        "latestVerdict",
    ]
    assert [item["idShort"] for item in simulation["submodelElements"]] == [
        "activeFeaJobId",
        "lastCompletedFeaJobId",
    ]
    assert evaluation["submodelElements"][3]["value"] == "SAFE"


def test_read_projected_view_uses_basyx_payload_not_sql():
    aas_id = "urn:bg:mieum:drw:04"

    class FakeClient:
        enabled = True

        def get_submodel(self, identifier):
            assert identifier == submodel_id(aas_id, identifier.rsplit("/", 1)[-1])
            name = identifier.rsplit("/", 1)[-1]
            values = {
                "ProcessState": [
                    {"idShort": "reductionRatio", "value": "0.3"},
                    {"idShort": "quality", "value": "GOOD"},
                    {"idShort": "stateVersion", "value": "state-0001"},
                ],
                "EvaluationState": [
                    {"idShort": "latestEvaluationId", "value": "eval-1"},
                    {"idShort": "latestSnapshotId", "value": "snap-1"},
                    {"idShort": "latestDecisionId", "value": "dec-1"},
                    {"idShort": "latestVerdict", "value": "SAFE"},
                ],
                "SimulationState": [
                    {"idShort": "activeFeaJobId", "value": None},
                    {"idShort": "lastCompletedFeaJobId", "value": "fea-1"},
                ],
            }
            return {"submodelElements": values[name]}

    view = read_projected_view(FakeClient(), PRIMARY)
    assert view["basyx_status"] == "ONLINE"
    assert view["aas_id"] == aas_id
    assert view["process"]["reductionRatio"] == "0.3"
    assert view["evaluation"]["latestDecisionId"] == "dec-1"
    assert view["evaluation"]["latestVerdict"] == "SAFE"
    assert view["simulation"]["lastCompletedFeaJobId"] == "fea-1"


def test_read_projected_view_offline_when_disabled():
    from cold_drawing_twin.twin.basyx import BasyxClient

    view = read_projected_view(BasyxClient("http://basyx.example", enabled=False), PRIMARY)
    assert view["basyx_status"] == "OFFLINE"
    assert view["process"] is None
    assert view["evaluation"] is None
    assert view["simulation"] is None


def test_read_projected_view_offline_on_basyx_error():
    class FakeClient:
        enabled = True

        def get_submodel(self, identifier):
            raise ConnectionError("basyx down")

    view = read_projected_view(FakeClient(), PRIMARY)
    assert view["basyx_status"] == "OFFLINE"
    assert view["evaluation"] is None


def test_get_submodel_uses_unpadded_base64url(monkeypatch):
    from cold_drawing_twin.twin.basyx import BasyxClient

    seen = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"submodelElements": []}

    def fake_request(self, method, path, json=None, raise_for_status=True):
        seen.append(path)
        return Response()

    monkeypatch.setattr(BasyxClient, "_request", fake_request)
    client = BasyxClient("http://basyx.example", enabled=True)
    identifier = submodel_id("urn:bg:mieum:drw:04", "EvaluationState")
    client.get_submodel(identifier)
    assert seen == [f"/submodels/{encode_id(identifier)}"]
    assert "=" not in encode_id(identifier)
