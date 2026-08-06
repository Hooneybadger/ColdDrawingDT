from pathlib import Path

from cold_drawing_twin.simulation.postprocess.parser import parse_solver_identity
from cold_drawing_twin.simulation.validation import (
    build_validation_report,
    geometry_sensitivity_direction,
    mesh_refinement_structure,
    mesh_repeatability,
    solver_artifacts,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_identical_snapshot_mesh_checksums(tmp_path: Path):
    report = mesh_repeatability(tmp_path)
    assert report["same_checksum"] is True
    assert report["checksum"]
    assert report["element_count"] > 10


def test_finer_mesh_has_more_elements_and_new_checksum(tmp_path: Path):
    report = mesh_refinement_structure(tmp_path)
    assert report["fine_has_more_elements"] is True
    assert report["checksums_differ"] is True


def test_higher_reduction_maps_to_smaller_final_radius():
    report = geometry_sensitivity_direction()
    assert report["higher_reduction_smaller_rf"] is True


def test_missing_work_dir_does_not_invent_solver_metrics():
    report = solver_artifacts(None)
    assert report["present"] is False
    assert report["invented"] is False
    assert "final_outer_radius_m" not in report


def test_validation_report_reads_listing_fixture_without_inventing(tmp_path: Path):
    work = tmp_path / "job"
    work.mkdir()
    (work / "engine.out").write_text((FIXTURES / "engine.out").read_text(encoding="utf-8"), encoding="utf-8")
    result = {
        "solver_status": "SUCCEEDED",
        "quality_pass": True,
        "criterion_verdict": "INCONCLUSIVE",
        "metrics": {
            "internal_energy": 125.0,
            "kinetic_energy": 0.41,
            "drawing_force_n": 8750.0,
            "final_outer_radius_m": None,
            "mesh": {"checksum": "abc", "element_count": 12},
        },
    }
    (work / "result.json").write_text(__import__("json").dumps(result), encoding="utf-8")
    report = build_validation_report(tmp_path / "scratch", work)
    assert report["invented_physics"] is False
    assert report["solver_artifacts"]["internal_energy"] == 125.0
    assert report["solver_artifacts"]["drawing_force_n"] == 8750.0
    assert report["solver_artifacts"]["final_outer_radius_m"] is None


def test_parse_solver_identity_from_version_line():
    text = "OpenRadioss\nVERSION : latest-20260728\n NORMAL TERMINATION\n"
    identity = parse_solver_identity(text)
    assert identity["solver"] == "OpenRadioss"
    assert identity["version"] == "latest-20260728"
    assert identity["source"] == "listing"


def test_parse_solver_identity_empty_listing():
    identity = parse_solver_identity("")
    assert identity["version"] is None
    assert identity["source"] is None
