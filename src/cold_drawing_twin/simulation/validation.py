from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.simulation.preprocess.geometry import build_geometry
from cold_drawing_twin.simulation.preprocess.mesh import generate_mesh
from cold_drawing_twin.simulation.preprocess.parameter_mapping import map_process
from cold_drawing_twin.simulation.postprocess.parser import parse_solver_identity, parse_solver_outputs

DEMO = ProcessFeatures(0.3, 0.2, 0.08, 0.7)


def _geometry_and_mesh(work_dir: Path, features: ProcessFeatures, **mesh_kwargs: int) -> dict[str, Any]:
    mapped = map_process(features)
    geometry = build_geometry(
        r0=float(mapped["initial_radius_m"]),
        rf=float(mapped["final_radius_m"]),
        die_half_angle_rad=float(mapped["die_half_angle_rad"]),
        inlet_length_m=float(mapped["inlet_length_m"]),
        outlet_length_m=float(mapped["outlet_length_m"]),
        clearance_m=float(mapped["clearance_m"]),
    )
    mesh = generate_mesh(
        work_dir,
        geometry,
        float(mapped["deformation_zone_size_m"]),
        float(mapped["far_field_size_m"]),
        **mesh_kwargs,
    )
    return {"mapped": mapped, "geometry": geometry, "mesh": mesh}


def mesh_repeatability(work_dir: Path, features: ProcessFeatures = DEMO) -> dict[str, Any]:
    first = _geometry_and_mesh(work_dir / "a", features, radial_elements=4, axial_elements=12, die_elements=6)
    second = _geometry_and_mesh(work_dir / "b", features, radial_elements=4, axial_elements=12, die_elements=6)
    checksum = first["mesh"]["checksum"]
    return {
        "same_checksum": checksum == second["mesh"]["checksum"],
        "checksum": checksum,
        "element_count": first["mesh"]["element_count"],
    }


def mesh_refinement_structure(work_dir: Path, features: ProcessFeatures = DEMO) -> dict[str, Any]:
    coarse = _geometry_and_mesh(work_dir / "coarse", features, radial_elements=4, axial_elements=12, die_elements=6)
    fine = _geometry_and_mesh(work_dir / "fine", features, radial_elements=8, axial_elements=24, die_elements=12)
    return {
        "note": "Structure only. Not a published mesh-convergence study.",
        "coarse": {
            "checksum": coarse["mesh"]["checksum"],
            "element_count": coarse["mesh"]["element_count"],
        },
        "fine": {
            "checksum": fine["mesh"]["checksum"],
            "element_count": fine["mesh"]["element_count"],
        },
        "fine_has_more_elements": fine["mesh"]["element_count"] > coarse["mesh"]["element_count"],
        "checksums_differ": coarse["mesh"]["checksum"] != fine["mesh"]["checksum"],
    }


def geometry_sensitivity_direction() -> dict[str, Any]:
    low = map_process(ProcessFeatures(0.2, 0.2, 0.08, 0.7))
    high = map_process(ProcessFeatures(0.4, 0.2, 0.08, 0.7))
    return {
        "note": "Mapped final radius vs reduction_ratio. Not a live Engine sweep.",
        "rf_at_reduction_0_2_m": low["final_radius_m"],
        "rf_at_reduction_0_4_m": high["final_radius_m"],
        "higher_reduction_smaller_rf": float(high["final_radius_m"]) < float(low["final_radius_m"]),
    }


def solver_artifacts(work_dir: Path | None) -> dict[str, Any]:
    if work_dir is None or not work_dir.exists():
        return {"present": False, "invented": False, "reason": "work_dir missing"}
    result_path = work_dir / "result.json"
    parsed = parse_solver_outputs(work_dir) if any(work_dir.iterdir()) else None
    payload: dict[str, Any] = {"present": True, "invented": False, "work_dir": str(work_dir)}
    if result_path.exists():
        stored = json.loads(result_path.read_text(encoding="utf-8"))
        metrics = stored.get("metrics") or {}
        payload["result_json"] = str(result_path)
        payload["solver_status"] = stored.get("solver_status")
        payload["quality_pass"] = stored.get("quality_pass")
        payload["criterion_verdict"] = stored.get("criterion_verdict")
        payload["final_outer_radius_m"] = metrics.get("final_outer_radius_m")
        payload["drawing_force_n"] = metrics.get("drawing_force_n")
        payload["internal_energy"] = metrics.get("internal_energy")
        payload["kinetic_energy"] = metrics.get("kinetic_energy")
        payload["energy_error"] = metrics.get("energy_error")
        payload["mesh"] = metrics.get("mesh")
        payload["solver_binaries"] = stored.get("solver_binaries")
        payload["solver_identity"] = metrics.get("solver_identity") or stored.get("solver_identity")
    elif parsed is not None:
        payload["result_json"] = None
        payload["solver_identity"] = parsed.get("solver_identity") or parse_solver_identity("")
        payload["termination"] = parsed.get("termination")
        payload["metrics"] = parsed.get("metrics")
    else:
        payload["present"] = False
        payload["reason"] = "no result.json or listing"
    return payload


def build_validation_report(scratch_dir: Path, work_dir: Path | None = None) -> dict[str, Any]:
    return {
        "invented_physics": False,
        "mesh_repeatability": mesh_repeatability(scratch_dir / "repeat"),
        "mesh_refinement_structure": mesh_refinement_structure(scratch_dir / "refine"),
        "geometry_sensitivity_direction": geometry_sensitivity_direction(),
        "solver_artifacts": solver_artifacts(work_dir),
    }
