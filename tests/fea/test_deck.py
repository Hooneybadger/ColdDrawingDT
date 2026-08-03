from pathlib import Path

from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.simulation.preprocess.geometry import build_geometry
from cold_drawing_twin.simulation.preprocess.mesh import generate_mesh
from cold_drawing_twin.simulation.preprocess.parameter_mapping import map_process
from cold_drawing_twin.simulation.preprocess.radioss_deck import write_radioss_decks


def _mesh(tmp_path: Path):
    mapped = map_process(ProcessFeatures(0.3, 0.2, 0.08, 0.7))
    geometry = build_geometry(
        r0=float(mapped["initial_radius_m"]),
        rf=float(mapped["final_radius_m"]),
        die_half_angle_rad=float(mapped["die_half_angle_rad"]),
        inlet_length_m=float(mapped["inlet_length_m"]),
        outlet_length_m=float(mapped["outlet_length_m"]),
        clearance_m=float(mapped["clearance_m"]),
    )
    mesh = generate_mesh(
        tmp_path,
        geometry,
        0.0008,
        0.002,
        radial_elements=4,
        axial_elements=16,
        die_elements=8,
    )
    return geometry, mesh


def test_axisymmetric_quad_mesh(tmp_path: Path):
    geometry, mesh = _mesh(tmp_path)
    assert mesh["workpiece"]["element_count"] == 4 * 16
    assert mesh["die"]["element_count"] == 8
    ys = [node[2] for node in mesh["workpiece"]["nodes"]]
    assert min(ys) >= 0.0
    assert max(ys) == geometry.r0
    assert (tmp_path / "drawing.geo").exists()
    assert (tmp_path / "mesh.json").exists()


def test_radioss_deck_is_axisymmetric_drawing_model(tmp_path: Path):
    geometry, mesh = _mesh(tmp_path)
    decks = write_radioss_decks(tmp_path, geometry, mesh, 0.08, "fea-smoke")
    starter = Path(decks["starter"]).read_text(encoding="utf-8")
    engine = Path(decks["engine"]).read_text(encoding="utf-8")
    assert "/ANALY" in starter
    assert "/QUAD/1" in starter
    assert "/SH3N/" not in starter
    assert "/INTER/TYPE5/1" in starter
    assert "       000                   2         0" in starter
    assert "/IMPVEL/1" in starter
    assert "/MAT/PLAS_TAB/1" in starter
    assert "/SURF/SEG/1" in starter
    assert "0.08" in starter or "8.000000000000E-02" in starter
    assert "stainless_reference_v1" in starter
    assert "production_calibrated False" in starter
    assert "/RUN/" in engine
    assert "/ANIM/ELEM/VONM" in engine
    assert "/ANIM/ELEM/EPSP" in engine
