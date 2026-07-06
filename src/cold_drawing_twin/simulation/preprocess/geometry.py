from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AxisymmetricGeometry:
    r0: float
    rf: float
    die_half_angle_rad: float
    inlet_length_m: float
    outlet_length_m: float
    cone_length_m: float
    total_length_m: float


def build_geometry(
    *,
    r0: float,
    rf: float,
    die_half_angle_rad: float,
    inlet_length_m: float,
    outlet_length_m: float,
) -> AxisymmetricGeometry:
    if die_half_angle_rad <= 0:
        raise ValueError("die_half_angle_rad must be positive")
    cone_length_m = (r0 - rf) / math.tan(die_half_angle_rad)
    return AxisymmetricGeometry(
        r0=r0,
        rf=rf,
        die_half_angle_rad=die_half_angle_rad,
        inlet_length_m=inlet_length_m,
        outlet_length_m=outlet_length_m,
        cone_length_m=cone_length_m,
        total_length_m=inlet_length_m + cone_length_m + outlet_length_m,
    )


def write_geo(path, geometry: AxisymmetricGeometry, deformation_size: float, far_size: float) -> None:
    z0 = 0.0
    z1 = geometry.inlet_length_m
    z2 = geometry.inlet_length_m + geometry.cone_length_m
    z3 = geometry.total_length_m
    content = f"""SetFactory("OpenCASCADE");
// 2D axisymmetric workpiece. r is X, drawing axis is Y.
Point(1) = {{0, {z0}, 0, {far_size}}};
Point(2) = {{{geometry.r0}, {z0}, 0, {far_size}}};
Point(3) = {{{geometry.r0}, {z1}, 0, {deformation_size}}};
Point(4) = {{{geometry.rf}, {z2}, 0, {deformation_size}}};
Point(5) = {{{geometry.rf}, {z3}, 0, {far_size}}};
Point(6) = {{0, {z3}, 0, {far_size}}};
Line(1) = {{1, 2}};
Line(2) = {{2, 3}};
Line(3) = {{3, 4}};
Line(4) = {{4, 5}};
Line(5) = {{5, 6}};
Line(6) = {{6, 1}};
Curve Loop(1) = {{1, 2, 3, 4, 5, 6}};
Plane Surface(1) = {{1}};
Physical Surface("workpiece") = {{1}};
Mesh.CharacteristicLengthMin = {deformation_size};
Mesh.CharacteristicLengthMax = {far_size};
"""
    path.write_text(content, encoding="utf-8")
