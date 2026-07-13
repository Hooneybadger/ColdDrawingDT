from pathlib import Path

from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.simulation.preprocess.geometry import build_geometry
from cold_drawing_twin.simulation.preprocess.mesh import generate_mesh
from cold_drawing_twin.simulation.preprocess.parameter_mapping import map_process


def test_gmsh_axisymmetric_mesh(tmp_path: Path):
    mapped = map_process(ProcessFeatures(0.3, 0.2, 0.08, 0.7))
    geometry = build_geometry(
        r0=float(mapped["initial_radius_m"]),
        rf=float(mapped["final_radius_m"]),
        die_half_angle_rad=float(mapped["die_half_angle_rad"]),
        inlet_length_m=float(mapped["inlet_length_m"]),
        outlet_length_m=float(mapped["outlet_length_m"]),
    )
    mesh = generate_mesh(tmp_path, geometry, 0.0008, 0.002)
    assert mesh["node_count"] > 10
    assert mesh["element_count"] > 10
    assert mesh["checksum"]
