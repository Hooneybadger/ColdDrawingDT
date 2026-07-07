from __future__ import annotations

from cold_drawing_twin.config_files import fea_reference
from cold_drawing_twin.domain.features import ProcessFeatures


def final_radius_m(reduction_ratio: float, initial_radius_m: float) -> float:
    if reduction_ratio >= 1:
        raise ValueError("reduction_ratio must be < 1")
    return initial_radius_m * (1.0 - reduction_ratio) ** 0.5


def map_process(features: ProcessFeatures) -> dict[str, float | str]:
    reference = fea_reference()
    initial_radius_m = float(reference["geometry"]["initial_radius_m"])
    return {
        "initial_radius_m": initial_radius_m,
        "final_radius_m": final_radius_m(features.reduction_ratio, initial_radius_m),
        "die_half_angle_rad": features.die_half_angle_rad,
        "friction_coefficient": features.friction_coefficient,
        "normalized_hardening_coefficient": features.normalized_hardening_coefficient,
        "material_profile_id": reference["material"]["profile_id"],
        "mapping_version": reference["material"]["mapping_version"],
        "inlet_length_m": float(reference["geometry"]["inlet_length_m"]),
        "outlet_length_m": float(reference["geometry"]["outlet_length_m"]),
        "deformation_zone_size_m": float(reference["mesh"]["deformation_zone_size_m"]),
        "far_field_size_m": float(reference["mesh"]["far_field_size_m"]),
    }
