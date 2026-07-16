from cold_drawing_twin.inference.pinn.adapter import map_released_payload


def test_maps_released_predict_json():
    payload = {
        "decision": "NEED_FEA",
        "normalized_stress": 0.1,
        "illustrative_damage": 0.2,
        "physics_residual_max": 0.01,
        "safe_probability": None,
        "supported_range": True,
        "model_version": "poc-v0.1.1",
    }
    result = map_released_payload(payload, contract_version="v0.1.1")
    assert result.verdict == "NEED_FEA"
    assert result.stress_indicator == 0.1
    assert result.damage_indicator == 0.2
    assert result.physics_residual == 0.01
    assert result.confidence is None
    assert result.model_version == "v0.1.1"
