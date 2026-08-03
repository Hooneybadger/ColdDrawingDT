from cold_drawing_twin.twin.basyx import (
    drawing_aas_shell,
    encode_id,
    evaluation_submodel,
    process_submodel,
    simulation_submodel,
)


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
