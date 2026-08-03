from cold_drawing_twin.simulation.preprocess.material import load_reference_material


def test_reference_material_is_not_mill_calibrated():
    material = load_reference_material()
    assert material["id"] == "stainless_reference_v1"
    assert material["production_calibrated"] is False
    assert material["calibrated"] is False
    assert material["curve"][0][0] == 0.0
    assert abs(material["curve"][0][1] - 389.67e6) < 1.0
    assert material["young_modulus_pa"] == 2.21e11
    assert "altair" in material["source"]["citation"].lower()
