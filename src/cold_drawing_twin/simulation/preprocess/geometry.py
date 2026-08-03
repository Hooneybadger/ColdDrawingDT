from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AxisymmetricGeometry:
    """Round-bar drawing in the Radioss 2D YZ plane: Y radial, Z axis of revolution."""

    r0: float
    rf: float
    die_half_angle_rad: float
    inlet_length_m: float
    outlet_length_m: float
    cone_length_m: float
    bar_length_m: float
    clearance_m: float
    die_thickness_m: float


def build_geometry(
    *,
    r0: float,
    rf: float,
    die_half_angle_rad: float,
    inlet_length_m: float,
    outlet_length_m: float,
    clearance_m: float = 1.0e-4,
    extra_bar_m: float | None = None,
) -> AxisymmetricGeometry:
    if die_half_angle_rad <= 0:
        raise ValueError("die_half_angle_rad must be positive")
    if rf >= r0:
        raise ValueError("final radius must be smaller than initial radius")
    cone_length_m = (r0 - rf) / math.tan(die_half_angle_rad)
    extra = extra_bar_m if extra_bar_m is not None else -min(2.0e-3, 0.05 * inlet_length_m)
    # Nose stays inside the cylindrical inlet, short of the cone corner.
    bar_length_m = extra + inlet_length_m
    return AxisymmetricGeometry(
        r0=r0,
        rf=rf,
        die_half_angle_rad=die_half_angle_rad,
        inlet_length_m=inlet_length_m,
        outlet_length_m=outlet_length_m,
        cone_length_m=cone_length_m,
        bar_length_m=bar_length_m,
        clearance_m=clearance_m,
        die_thickness_m=max(0.5 * (r0 - rf), 5.0e-4),
    )


def die_inner_radius(geometry: AxisymmetricGeometry, z: float) -> float:
    """Stationary die bore vs axial coordinate Z (drawing axis)."""
    z_in = geometry.inlet_length_m
    z_cone = z_in + geometry.cone_length_m
    r_in = geometry.r0 + geometry.clearance_m
    r_out = geometry.rf + geometry.clearance_m
    if z <= z_in:
        return r_in
    if z >= z_cone:
        return r_out
    t = (z - z_in) / geometry.cone_length_m
    return r_in + t * (r_out - r_in)


def die_profile_points(geometry: AxisymmetricGeometry, n_seg: int) -> list[tuple[float, float]]:
    n_seg = max(n_seg, 4)
    z0 = 0.0
    z1 = geometry.inlet_length_m + geometry.cone_length_m + geometry.outlet_length_m
    points: list[tuple[float, float]] = []
    for i in range(n_seg + 1):
        z = z0 + (z1 - z0) * i / n_seg
        points.append((die_inner_radius(geometry, z), z))
    return points
