from __future__ import annotations

import argparse
import json
from pathlib import Path

from cold_drawing_twin.config_files import fea_reference, hardening_map
from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.settings import load_settings
from cold_drawing_twin.simulation.postprocess.damage import damage_metrics
from cold_drawing_twin.simulation.postprocess.energy import parse_energy_histories
from cold_drawing_twin.simulation.postprocess.fields import parse_anim_or_placeholder
from cold_drawing_twin.simulation.postprocess.force import parse_drawing_force
from cold_drawing_twin.simulation.postprocess.safety_criterion import apply_criterion, quality_pass
from cold_drawing_twin.simulation.preprocess.geometry import build_geometry
from cold_drawing_twin.simulation.preprocess.mesh import generate_mesh
from cold_drawing_twin.simulation.preprocess.parameter_mapping import map_process
from cold_drawing_twin.simulation.preprocess.radioss_deck import write_radioss_decks
from cold_drawing_twin.simulation.solver.openradioss import SolverError, run_openradioss


def run_case(
    features: ProcessFeatures,
    work_dir: Path,
    job_id: str = "fea-smoke",
    *,
    run_solver: bool = True,
) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    mapped = map_process(features)
    geometry = build_geometry(
        r0=float(mapped["initial_radius_m"]),
        rf=float(mapped["final_radius_m"]),
        die_half_angle_rad=float(mapped["die_half_angle_rad"]),
        inlet_length_m=float(mapped["inlet_length_m"]),
        outlet_length_m=float(mapped["outlet_length_m"]),
    )
    mesh = generate_mesh(
        work_dir,
        geometry,
        float(mapped["deformation_zone_size_m"]),
        float(mapped["far_field_size_m"]),
    )
    decks = write_radioss_decks(
        work_dir,
        geometry,
        mesh,
        float(mapped["friction_coefficient"]),
        job_id,
    )
    solver_status = "SKIPPED"
    solver_error = None
    settings = load_settings()
    mapping = hardening_map()
    if mapping.get("plastic_curve") is None:
        run_solver = False
        solver_status = "FAILED"
        solver_error = "hardening-map-v1 has no calibrated plastic curve"
    elif run_solver:
        try:
            run_openradioss(
                starter_bin=settings.openradioss_starter_bin,
                engine_bin=settings.openradioss_engine_bin,
                starter_file=Path(decks["starter"]),
                engine_file=Path(decks["engine"]),
                work_dir=work_dir,
                timeout_s=settings.fea_job_timeout_s,
            )
            solver_status = "SUCCEEDED"
        except SolverError as exc:
            solver_status = exc.status
            solver_error = str(exc)
    histories = parse_energy_histories(work_dir)
    forces = parse_drawing_force(work_dir)
    fields = parse_anim_or_placeholder(work_dir)
    histories["drawing_force"] = forces.get("drawing_force") or []
    ok, quality_reason = quality_pass(histories)
    metrics = {
        "geometry": {
            "r0": geometry.r0,
            "rf": geometry.rf,
            "cone_length_m": geometry.cone_length_m,
        },
        "mesh": {
            "node_count": mesh["node_count"],
            "element_count": mesh["element_count"],
            "checksum": mesh["checksum"],
        },
        "fields": fields,
        "histories": {key: values[-1] if values else None for key, values in histories.items()},
        "damage": damage_metrics(fields),
        "fea_profile_version": fea_reference()["version"],
        "material_mapping_version": mapping["version"],
        "mesh_config_version": fea_reference()["mesh"]["profile_version"],
    }
    verdict, criterion_reason = apply_criterion(quality_ok=ok, metrics=metrics)
    result = {
        "job_id": job_id,
        "solver_status": solver_status,
        "solver_error": solver_error,
        "quality_pass": ok,
        "quality_reason": quality_reason,
        "criterion_verdict": verdict.value,
        "criterion_reason": criterion_reason,
        "metrics": metrics,
        "decks": decks,
        "work_dir": str(work_dir),
    }
    (work_dir / "result.json").write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Gmsh and OpenRadioss for one drawing case.")
    parser.add_argument("--reduction-ratio", type=float, required=True)
    parser.add_argument("--die-angle-rad", type=float, required=True)
    parser.add_argument("--friction", type=float, required=True)
    parser.add_argument("--hardening", type=float, required=True)
    parser.add_argument("--work-dir", type=Path, default=Path("simulation/workspaces/cli"))
    parser.add_argument("--job-id", default="fea-cli")
    args = parser.parse_args(argv)
    features = ProcessFeatures(
        reduction_ratio=args.reduction_ratio,
        die_half_angle_rad=args.die_angle_rad,
        friction_coefficient=args.friction,
        normalized_hardening_coefficient=args.hardening,
    )
    result = run_case(features, args.work_dir, args.job_id)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result["solver_status"] == "SUCCEEDED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
