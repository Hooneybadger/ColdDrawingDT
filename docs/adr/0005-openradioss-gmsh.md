# ADR 0005 - OpenRadioss and Gmsh

## Context

The FEA fallback must solve a parameterized cold-drawing reference case with large plastic strain and friction, using tools we can rerun.

## Decision

Use the Gmsh Python API for geometry and mesh. Use OpenRadioss as the explicit nonlinear solver. Start with a 2D axisymmetric round-bar model.

## Consequence

Quasi-static quality must be proven from energy and force histories. Solver completion alone is not a safety verdict.
