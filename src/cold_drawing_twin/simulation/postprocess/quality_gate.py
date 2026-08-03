from __future__ import annotations

import math
from typing import Any

from cold_drawing_twin.config_files import fea_quality
from cold_drawing_twin.simulation.preprocess.material import load_reference_material


def evaluate_quality(
    *,
    solver_status: str,
    parsed: dict[str, Any],
    mesh: dict[str, Any],
) -> tuple[bool, str]:
    """Accept solver output only when documented checks pass. No invented cut-offs."""
    policy = fea_quality()
    reasons: list[str] = []
    if policy.get("require_normal_termination", True):
        termination = (parsed.get("termination") or {}).get("status")
        if solver_status != "SUCCEEDED" or termination != "NORMAL_TERMINATION":
            reasons.append(f"solver_status={solver_status} termination={termination}")
    required_files = ["starter.stdout.log", "engine.stdout.log"]
    files = set(parsed.get("files") or [])
    missing_files = [name for name in required_files if name not in files]
    if missing_files:
        reasons.append(f"missing files: {missing_files}")
    histories = parsed.get("histories") or {}
    for name in policy.get("require_histories") or []:
        if not histories.get(name):
            reasons.append(f"missing history {name}")
    metrics = parsed.get("metrics") or {}
    for name in policy.get("require_metrics") or []:
        if metrics.get(name) is None:
            reasons.append(f"missing metric {name}")
    if policy.get("reject_nonfinite", True):
        for name, value in metrics.items():
            if value is None:
                continue
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                reasons.append(f"non-finite metric {name}")
    min_quads = int(policy.get("min_workpiece_quads") or 0)
    min_nodes = int(policy.get("min_workpiece_nodes") or 0)
    work = mesh.get("workpiece") or {}
    if work.get("element_count", mesh.get("element_count", 0)) < min_quads:
        reasons.append("workpiece element count below minimum")
    if work.get("node_count", mesh.get("node_count", 0)) < min_nodes:
        reasons.append("workpiece node count below minimum")
    material = load_reference_material()
    young = material["young_modulus_pa"]
    vm = metrics.get("peak_von_mises_pa")
    if isinstance(vm, (int, float)) and vm > young:
        reasons.append("peak von Mises exceeds reference Young's modulus")
    plastic = metrics.get("peak_plastic_strain")
    if isinstance(plastic, (int, float)) and plastic < 0:
        reasons.append("negative plastic strain")
    if policy.get("reject_saturated_energy_error", False):
        limit = float(policy.get("saturated_energy_error", 0.999))
        err = metrics.get("energy_error")
        if isinstance(err, (int, float)) and abs(float(err)) >= limit:
            reasons.append("OpenRadioss energy error saturated at 99.9%")
    if reasons:
        return False, "; ".join(reasons)
    return True, "normal termination, required files, finite required metrics"
