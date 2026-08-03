from cold_drawing_twin.simulation.preprocess.parameter_mapping import final_radius_m, map_process
from cold_drawing_twin.domain.features import ProcessFeatures


def test_reduction_to_final_radius():
    rf = final_radius_m(0.3, 0.01)
    assert abs(rf - 0.01 * (0.7**0.5)) < 1e-12


def test_map_keeps_hardening_as_normalized_scalar():
    mapped = map_process(ProcessFeatures(0.3, 0.2, 0.08, 0.7))
    assert mapped["normalized_hardening_coefficient"] == 0.7
    assert mapped["mapping_version"] == "hardening-map-v1"
    assert abs(mapped["final_radius_m"] - 0.008366600265340756) < 1e-9
    assert mapped["friction_is_contact_parameter"] is True


def test_idempotency_key_changes_with_profile():
    from cold_drawing_twin.domain.lineage import idempotency_hash

    a = idempotency_hash("snap-1", "fea-reference-v1", "hardening-map-v1", "mesh-v1", "unset", "fea-criterion-v1")
    b = idempotency_hash("snap-1", "fea-reference-v1", "hardening-map-v1", "mesh-v2", "unset", "fea-criterion-v1")
    assert a != b
