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

