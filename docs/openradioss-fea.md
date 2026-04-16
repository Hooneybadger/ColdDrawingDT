# OpenRadioss FEA

Terms: [glossary](glossary.md).

Goal: an executable FEA fallback for cold drawing.

```text
Process features
  -> physical mapping
  -> Gmsh axisymmetric geometry and mesh
  -> OpenRadioss Starter and Engine
  -> raw output
  -> postprocess
  -> versioned safety criterion
```

This version has the reference profile only. It does not run Gmsh or OpenRadioss yet.

## Why OpenRadioss

Cold drawing has large plastic strain and sliding friction. OpenRadioss is an explicit nonlinear solver that can run 2D axisymmetric elastoplastic contact.

The process is quasi-static. Explicit time stepping is allowed only if energy and force checks show that fake inertia is not driving the answer.

## First model

First case: round bar, 2D axisymmetric.

Geometry:

- Start radius from the reference profile
- Final radius from `reduction_ratio`
- Die cone from `die_half_angle_rad`
- Enough inlet and outlet contact length
- Rigid or very stiff die

Circular reduction:

```text
A_f = A_0 * (1 - reduction_ratio)
r_f = r_0 * sqrt(1 - reduction_ratio)
```

Demo Snapshot uses `reduction_ratio = 0.3` and `initial_radius_m = 0.01` from [config/fea_reference_case.yaml](../config/fea_reference_case.yaml):

```text
r_0 = 0.01 m
r_f = 0.01 * sqrt(1 - 0.3) = 0.00837 m
```

## Material mapping

PINN field `normalized_hardening_coefficient` is not MPa.

This version records IDs only:

- `material_profile_id: stainless_reference_v1`
- `mapping_version: hardening-map-v1`

The curve numbers are not in the repository yet. Do not treat the normalized scalar as a physical unit. A later calibrated card can replace the mapping without changing Evaluation contracts.

## Contact

`friction_coefficient` maps to die/material friction. Contact and penalty settings live in a versioned FEA profile, not as hidden constants. Demo value: `0.08`.

