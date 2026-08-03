from __future__ import annotations

from typing import Any

from cold_drawing_twin.config_files import hardening_map, load_yaml


class MaterialConfigError(ValueError):
    pass


def load_reference_material() -> dict[str, Any]:
    mapping = hardening_map()
    rel = mapping.get("reference_profile_file")
    if not rel:
        raise MaterialConfigError("hardening_map.yaml has no reference_profile_file")
    profile = load_yaml(str(rel))
    if profile.get("source", {}).get("production_calibrated") is True:
        raise MaterialConfigError("reference FEA material must not claim production calibration")
    curve = profile.get("plastic", {}).get("curve") or []
    if len(curve) < 2:
        raise MaterialConfigError("reference plastic curve is missing")
    elastic = profile["elastic"]
    return {
        "id": profile["id"],
        "version": profile.get("version") or profile["id"],
        "mapping_version": mapping["version"],
        "calibrated": bool(mapping.get("calibrated")),
        "production_calibrated": False,
        "source": profile.get("source", {}),
        "density_kg_m3": float(elastic["density_kg_m3"]),
        "young_modulus_pa": float(elastic["young_modulus_pa"]),
        "poisson_ratio": float(elastic["poisson_ratio"]),
        "curve": [(float(p), float(s)) for p, s in curve],
    }
